import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from PIL import Image

import auth
import config
import gen_poster
import get_library
import get_poster
import main
import update_poster


class MediaAPIHandler(BaseHTTPRequestHandler):
    """模拟需要完整客户端身份和专用认证头的媒体服务器。"""

    def log_message(self, *args):
        pass

    def respond(self, status, data):
        self.send_response(status)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.requests.append((self.path, dict(self.headers), body))
        identity = self.headers.get("X-Emby-Authorization", "")
        if not identity.startswith(self.server.scheme + " ") or not all(
            field in identity for field in ('Client="', 'Device="', 'DeviceId="', 'Version="1.0.0"')
        ):
            self.respond(403, {})
        elif self.path == self.server.prefix + "/Users/AuthenticateByName":
            if self.server.deny_login:
                self.respond(403, {})
            elif json.loads(body) == {"Username": "本地用户", "Pw": "test-password"}:
                self.respond(200, {"User": {"Id": "user-1"}, "AccessToken": "test-token"})
            else:
                self.respond(401, {})
        elif self.headers.get("X-Emby-Token") != "test-token":
            self.respond(403, {})
        elif self.path == self.server.prefix + "/Items/library-1/Images/Primary":
            self.respond(204, {})
        else:
            self.respond(404, {})

    def do_GET(self):
        self.server.requests.append((self.path, dict(self.headers), b""))
        if self.headers.get("X-Emby-Token") != "test-token":
            self.respond(403, {})
        elif self.path == self.server.prefix + "/Library/MediaFolders":
            self.respond(200, {"Items": [{"Id": "library-1", "Name": "Anime"}]})
        elif self.path.startswith(self.server.prefix + "/Users/user-1/Items/"):
            self.respond(200, {"Items": [{"Id": "movie-1", "ImageTags": {"Primary": "tag"}}]})
        elif self.path == self.server.prefix + "/Items/movie-1/Images/Primary":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(self.server.poster_bytes)
        else:
            self.respond(404, {})


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MediaAPIHandler)
        cls.server.requests = []
        cls.server.deny_login = False
        poster = io.BytesIO()
        Image.new("RGB", (20, 30), (68, 74, 86)).save(poster, "JPEG")
        cls.server.poster_bytes = poster.getvalue()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def test_login_and_all_authenticated_operations(self):
        for server_type, prefix, scheme in (
            ("emby", "/proxy/emby", "Emby"),
            ("jellyfin", "/proxy/jellyfin", "MediaBrowser"),
        ):
            with self.subTest(server_type=server_type), tempfile.TemporaryDirectory() as folder:
                self.server.prefix = prefix
                self.server.scheme = scheme
                self.server.requests.clear()
                base_url = f"http://127.0.0.1:{self.server.server_port}{prefix}"
                login = auth.authenticate(base_url + "/", "本地用户", "test-password", server_type)
                self.assertEqual(login["base_url"], base_url)
                server_config = {
                    **config.JELLYFIN_CONFIG,
                    "SERVER_TYPE": server_type,
                    "BASE_URL": login["base_url"],
                    "USER_ID": login["user_id"],
                    "ACCESS_TOKEN": login["access_token"],
                }
                with patch.dict(config.JELLYFIN_CONFIG, server_config):
                    self.assertEqual(get_library.get_libraries(), [{"Id": "library-1", "Name": "Anime"}])
                    self.assertEqual(get_poster.get_items("library-1")[0]["Id"], "movie-1")
                    destination = os.path.join(folder, "poster.jpg")
                    self.assertTrue(get_poster.download_image("movie-1", destination, 1))
                    with Image.open(destination) as image:
                        self.assertEqual(image.size, (20, 30))
                    self.assertTrue(update_poster.upload_image("library-1", "base64-png", "Anime"))
                self.assertEqual(len(self.server.requests), 5)
                for _, headers, _ in self.server.requests[1:]:
                    self.assertEqual(headers["X-Emby-Token"], "test-token")
                    self.assertIn('UserId="user-1"', headers["X-Emby-Authorization"])
                self.assertEqual(self.server.requests[-1][1]["Content-Type"], "image/png")
                self.assertEqual(self.server.requests[-1][2], b"base64-png")

    def test_three_argument_emby_login_and_no_retry_on_forbidden(self):
        self.server.prefix = "/emby"
        self.server.scheme = "Emby"
        base_url = f"http://127.0.0.1:{self.server.server_port}/emby/"
        self.assertIsNotNone(auth.authenticate(base_url, "本地用户", "test-password"))
        self.server.requests.clear()
        self.server.deny_login = True
        try:
            self.assertIsNone(auth.authenticate(base_url, "本地用户", "test-password"))
            self.assertEqual(len(self.server.requests), 1)
        finally:
            self.server.deny_login = False

    def test_init_auth_passes_server_type_and_normalized_url(self):
        login = {"user_id": "user-1", "access_token": "test-token", "base_url": "https://example.com/emby"}
        with patch.dict(config.JELLYFIN_CONFIG, {
            "SERVER_TYPE": "emby", "BASE_URL": "https://example.com/emby/",
            "USER_NAME": "local-user", "PASSWORD": "password",
        }), patch("auth.authenticate", return_value=login) as authenticate:
            self.assertTrue(config.init_auth())
            authenticate.assert_called_once_with("https://example.com/emby/", "local-user", "password", "emby")
            self.assertEqual(config.JELLYFIN_CONFIG["BASE_URL"], login["base_url"])


class PosterTests(unittest.TestCase):
    def test_missing_or_incomplete_style_generates_real_png(self):
        styles = (
            [],
            [{"style_name": "other"}],
            [{"style_name": "style1", "style_ch_shadow": True}],
            [None, {"style_name": "style1", "style_ch_font": None, "style_eng_font": ""}],
        )
        with tempfile.TemporaryDirectory() as folder:
            poster_root = os.path.join(folder, "poster")
            os.makedirs(os.path.join(poster_root, "Anime"))
            Image.new("RGB", (80, 120), (68, 74, 86)).save(os.path.join(poster_root, "Anime", "1.jpg"))
            geometry = {
                **config.POSTER_GEN_CONFIG, "ROWS": 1, "COLS": 1,
                "CELL_WIDTH": 80, "CELL_HEIGHT": 120, "SAVE_COLUMNS": False,
            }
            for index, style in enumerate(styles):
                output = os.path.join(folder, f"output-{index}")
                with self.subTest(style=style), patch.multiple(
                    config, POSTER_FOLDER=poster_root, OUTPUT_FOLDER=output,
                    STYLE_CONFIGS=style, POSTER_GEN_CONFIG=geometry,
                    TEMPLATE_MAPPING=[{"library_name": "Anime", "library_ch_name": "动漫", "library_eng_name": "ANIME"}],
                ):
                    self.assertTrue(gen_poster.gen_poster_workflow("Anime"))
                    with Image.open(os.path.join(output, "Anime.png")) as image:
                        self.assertEqual(image.format, "PNG")
                        self.assertEqual(image.size, (1920, 1080))

    def test_failed_generation_skips_upload_and_continues_to_next_library(self):
        server = {**config.JELLYFIN_CONFIG, "UPDATE_POSTER": True}
        libraries = [{"Id": "failed", "Name": "Failed"}, {"Id": "good", "Name": "Good"}]
        with patch.object(config, "JELLYFIN_CONFIGS", [server]), patch.dict(config.JELLYFIN_CONFIG), \
                patch("main.get_libraries", return_value=libraries), \
                patch("main.download_posters_workflow", return_value=(True, 9)), \
                patch("main.gen_poster_workflow", side_effect=[False, True]), \
                patch("main.upload_poster_workflow") as upload:
            main.process_libraries()
            upload.assert_called_once_with("good", "Good")


if __name__ == "__main__":
    unittest.main()
