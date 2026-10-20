import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "extract-unfiltered"
LOADER = importlib.machinery.SourceFileLoader("extract_unfiltered", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
extract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = extract
LOADER.exec_module(extract)


class ExtractionTests(unittest.TestCase):
    def test_sort_groups_domains_and_nested_subdomains(self):
        domains = [
            "mail.yahoo.co.jp", "drive.google.com", "github.com",
            "www.google.com", "search.yahoo.co.jp", "docs.google.com",
            "example.co.jp", "a.drive.google.com",
        ]
        text = "\n".join("[link](https://{})".format(domain) for domain in domains)
        rows = extract.extract_rows(text, set())
        actual = [row.split("<code>")[1].split("</code>")[0] for row in rows]
        self.assertEqual(actual, [
            "github.com", "google.com", "docs.google.com", "drive.google.com",
            "a.drive.google.com", "example.co.jp", "mail.yahoo.co.jp",
            "search.yahoo.co.jp",
        ])

    def test_sort_uses_code_domain_and_preserves_order_within_domain(self):
        text = (
            "[https://z.test](https://blocked.test/first)\n"
            "[Z](https://a.test/z)\n"
            "[A](https://a.test/a)\n"
            "[https://b.test](https://blocked.test/last)\n"
        )
        rows = extract.extract_rows(text, {"blocked.test"})
        self.assertIn('href="https://a.test/z"', rows[0])
        self.assertIn('href="https://a.test/a"', rows[1])
        self.assertIn("<code>b.test</code>", rows[2])
        self.assertIn('href="https://blocked.test/last"', rows[2])
        self.assertIn("<code>z.test</code>", rows[3])

    def test_empty_title_uses_destination_hostname(self):
        for title in ("", " \t "):
            with self.subTest(title=title):
                rows = extract.extract_rows(
                    "[{}](https://www.google.com:443/path?q=1)".format(title), set())
                self.assertEqual(rows, [
                    '<li>[<code>google.com</code>] '
                    '<a href="https://www.google.com:443/path?q=1" '
                    'target="_blank">www.google.com</a></li>'
                ])

    def test_empty_title_uses_destination_not_other_url_on_line(self):
        rows = extract.extract_rows(
            "https://t.co/example [](<https://www.google.com>)", {"google.com"})
        self.assertEqual(rows, [
            '<li>[<code>t.co</code>] <a href="https://www.google.com" '
            'target="_blank">www.google.com</a></li>'
        ])

    def test_nested_title_urls_use_outer_destination(self):
        text = "[foo [https://t.co/ABCDEF](https://t.co/ABCDEF) bar](https://www.google.com/foo/bar)"
        rows = extract.extract_rows(text, {"google.com"})
        self.assertEqual(rows, [
            '<li>[<code>t.co</code>] <a href="https://www.google.com/foo/bar" '
            'target="_blank">foo [https://t.co/ABCDEF](https://t.co/ABCDEF) bar</a></li>'
        ])
        rows = extract.extract_rows(text, set())
        self.assertEqual(len(rows), 2)
        self.assertIn("<code>google.com</code>", rows[1])
        self.assertIn('href="https://www.google.com/foo/bar"', rows[1])

    def test_multiple_links_and_angle_destinations(self):
        text = "[A](<https://a.test/x>) [B](https://b.test/y)"
        rows = extract.extract_rows(text, set())
        self.assertEqual(len(rows), 2)
        self.assertIn('href="https://a.test/x" target="_blank">A</a>', rows[0])
        self.assertIn('href="https://b.test/y" target="_blank">B</a>', rows[1])

    def test_suffix_boundary_case_and_idn(self):
        blocked = {extract.normalize_domain("グーグル.com"), "google.com"}
        text = ("https://DRIVE.GOOGLE.COM./x https://notgoogle.com "
                "https://google.com.evil.test https://xn--qcka1pmc.com "
                "https://sub.グーグル.com")
        rows = extract.extract_rows(text, blocked)
        self.assertEqual(len(rows), 2)
        self.assertIn("<code>notgoogle.com</code>", rows[0])
        self.assertIn("<code>google.com.evil.test</code>", rows[1])

    def test_plain_text_parentheses_ports_and_ipv6(self):
        text = "(https://example.com:8443/wiki/Test_(thing)) https://[::1]/x"
        rows = extract.extract_rows(text, set())
        self.assertEqual(len(rows), 2)
        self.assertIn("<code>::1</code>", rows[0])
        self.assertIn('href="https://example.com:8443/wiki/Test_(thing)"', rows[1])

    def test_html_escaping(self):
        rows = extract.extract_rows('[<script>& "title"](https://a.test/?a=1&b=2)', set())
        self.assertIn("&lt;script&gt;&amp; &quot;title&quot;", rows[0])
        self.assertIn('href="https://a.test/?a=1&amp;b=2"', rows[0])

    def test_example_with_markdown_wrapped_destination(self):
        rows = extract.extract_rows(
            "[foo [https://t.co/a](https://t.co/a) bar]"
            "([https://www.google.com/x](https://www.google.com/x))",
            {"google.com"})
        self.assertEqual(len(rows), 1)
        self.assertIn('href="https://www.google.com/x"', rows[0])

    def test_recursive_config_comments_multiple_domains_and_symlink_cycle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first"
            second = root / "second"
            (first / "nested").mkdir(parents=True)
            second.mkdir()
            (first / "nested" / "block.conf").write_text(
                "# address=/commented.test/\n"
                "address=/google.com/yahoo.co.jp/ # trailing comment\n"
                "server=/allowed.test/#\nserver=/also-allowed.test/1.1.1.1\n"
                "address=/#/0.0.0.0\naddress=/#/127.0.0.1\n"
                "address=/zero.test/0.0.0.0\naddress=/loop.test/127.0.0.1\n"
                "address=/ipv6.test/::\naddress=/internal.test/192.168.82.1\n",
                encoding="utf-8")
            (second / "idn.conf").write_text("address=/グーグル.com/\n", encoding="utf-8")
            (second / "ignored.txt").write_text("address=/ignored.test/\n")
            (first / "linked").symlink_to(second, target_is_directory=True)
            (second / "cycle").symlink_to(first, target_is_directory=True)
            self.assertEqual(extract.blocked_domains([first, second]), {
                "google.com", "yahoo.co.jp", "zero.test", "loop.test",
                "ipv6.test", "xn--qcka1pmc.com"})

    def test_cli_paths_defaults_and_missing_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "dnsmasq").mkdir()
            (root / "private").mkdir()
            (root / "dnsmasq" / "block.conf").write_text("address=/blocked.test/\n")
            source = root / "input.md"
            source.write_text("[blocked](https://blocked.test) [open](https://open.test)\n")
            command = [sys.executable, str(SCRIPT), "input.md", "--dnsmasq-dir",
                       "dnsmasq," + str(root / "private")]
            for out, expected in [
                (None, root / "unfiltered.html"),
                ("reports", root / "reports" / "unfiltered.html"),
                ("reports/result.html", root / "reports" / "result.html"),
                (str(root / "absolute.html"), root / "absolute.html"),
                (str(root / "new-dir"), root / "new-dir" / "unfiltered.html"),
            ]:
                args = command + (["--out", out] if out else [])
                result = subprocess.run(args, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                content = expected.read_text()
                self.assertIn("<code>open.test</code>", content)
                self.assertNotIn("<code>blocked.test</code>", content)
            result = subprocess.run(command + ["--dnsmasq-dir", "missing"], cwd=root,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not exist", result.stderr)
            result = subprocess.run(command + ["--out", "input.md"], cwd=root,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not overwrite", result.stderr)

    def test_home_and_extension_based_paths(self):
        self.assertEqual(extract.expanded_path("~/example"), Path.home() / "example")
        self.assertEqual(extract.expanded_path("\\~/example"), Path.home() / "example")
        self.assertEqual(extract.output_path("foo/bar"), Path("foo/bar/unfiltered.html"))
        self.assertEqual(extract.output_path("foo/bar.html"), Path("foo/bar.html"))


if __name__ == "__main__":
    unittest.main()
