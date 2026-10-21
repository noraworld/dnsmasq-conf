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
    def test_shortcuts_and_rules_match_requested_format(self):
        title = 'foo/bar https://ghi.jkl.bit.ly/baz/qux - example.com'
        text = '[{}](https://abc.def.example.com/foo/bar)'.format(title)
        expected = (
            '<li>[ <code><a href="http://abc.def.example.com/foo/bar" target="_blank">http</a></code> / '
            '<code><a href="https://abc.def.example.com/foo/bar" target="_blank">https</a></code> / '
            '<code><a href="http://example.com" target="_blank">apex</a></code> / '
            '<code><a href="http://abc.def.example.com" target="_blank">subdomain</a></code> ] '
            '( <code>address=/example.com/</code> / <code>address=/abc.def.example.com/</code> / '
            '<code>address=/bit.ly/</code> / <code>address=/ghi.jkl.bit.ly/</code> ) '
            '<a href="https://abc.def.example.com/foo/bar">' + title + '</a></li>'
        )
        for blocked in (set(), {'example.com'}, {'bit.ly'}):
            with self.subTest(blocked=blocked):
                self.assertEqual(extract.extract_rows(text, blocked), [expected])
        self.assertEqual(extract.extract_rows(text, {'example.com', 'bit.ly'}), [])

    def test_apex_rules_are_unique_and_shortcuts_preserve_url_components(self):
        rows = extract.extract_rows(
            '[https://example.com/again](http://example.com:8080/p?q=1&b=2#part)', set())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].count('<code>address=/example.com/</code>'), 1)
        self.assertIn('href="http://example.com:8080/p?q=1&amp;b=2#part"', rows[0])
        self.assertIn('href="https://example.com:8080/p?q=1&amp;b=2#part"', rows[0])
        self.assertIn('href="http://example.com" target="_blank">apex', rows[0])
        self.assertIn('href="http://example.com" target="_blank">subdomain', rows[0])

    def test_apex_public_suffix_rules(self):
        for host, expected in [
            ('abc.def.example.com', 'example.com'),
            ('www.example.co.jp', 'example.co.jp'),
            ('www.example.co.uk', 'example.co.uk'),
            ('a.b.ck', 'a.b.ck'),  # wildcard public suffix
            ('a.www.ck', 'www.ck'),  # exception to wildcard
            ('www.city.kawasaki.jp', 'city.kawasaki.jp'),
            ('a.project.github.io', 'project.github.io'),  # private suffix
            ('sub.グーグル.com', 'xn--qcka1pmc.com'),
            ('127.0.0.1', '127.0.0.1'), ('::1', '::1'),
            ('localhost', 'localhost'),
        ]:
            with self.subTest(host=host):
                self.assertEqual(extract.apex_domain(host), expected)

    def test_sort_groups_domains_and_nested_subdomains(self):
        domains = [
            "mail.yahoo.co.jp", "drive.google.com", "github.com",
            "www.google.com", "search.yahoo.co.jp", "docs.google.com",
            "example.co.jp", "a.drive.google.com",
        ]
        text = "\n".join("[link](https://{})".format(domain) for domain in domains)
        rows = extract.extract_rows(text, set())
        actual = [row.split('href="http://')[1].split('"')[0] for row in rows]
        self.assertEqual(actual, [
            "github.com", "www.google.com", "docs.google.com", "drive.google.com",
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
        self.assertIn("<code>address=/b.test/</code>", rows[2])
        self.assertIn('href="https://blocked.test/last"', rows[2])
        self.assertIn("<code>address=/z.test/</code>", rows[3])

    def test_empty_title_uses_destination_hostname(self):
        for title in ("", " \t "):
            with self.subTest(title=title):
                rows = extract.extract_rows(
                    "[{}](https://www.google.com:443/path?q=1)".format(title), set())
                self.assertEqual(len(rows), 1)
                self.assertIn('<a href="https://www.google.com:443/path?q=1">www.google.com</a>', rows[0])


    def test_empty_title_uses_destination_not_other_url_on_line(self):
        rows = extract.extract_rows(
            "https://t.co/example [](<https://www.google.com>)", {"google.com"})
        self.assertEqual(len(rows), 1)
        self.assertIn('<a href="https://www.google.com">www.google.com</a>', rows[0])
        self.assertIn('address=/t.co/', rows[0])


    def test_nested_title_urls_use_outer_destination(self):
        text = "[foo [https://t.co/ABCDEF](https://t.co/ABCDEF) bar](https://www.google.com/foo/bar)"
        rows = extract.extract_rows(text, {"google.com"})
        self.assertEqual(len(rows), 1)
        self.assertIn('>foo [https://t.co/ABCDEF](https://t.co/ABCDEF) bar</a>', rows[0])
        self.assertIn('address=/t.co/', rows[0])
        self.assertIn('address=/www.google.com/', rows[0])
        self.assertEqual(extract.extract_rows(text, set()), rows)

    def test_grouping_preserves_separate_input_links(self):
        link = '[https://t.co/a](https://www.google.com/b)'
        single = extract.extract_rows(link, set())
        self.assertEqual(len(single), 1)
        self.assertEqual(extract.extract_rows(link + '\n' + link, set()), single * 2)
        self.assertEqual(extract.extract_rows(link + ' ' + link, set()), single * 2)
        for domain in ('google.com', 'www.google.com', 't.co'):
            self.assertIn('<code>address=/{}/</code>'.format(domain), single[0])


    def test_multiple_links_and_angle_destinations(self):
        text = "[A](<https://a.test/x>) [B](https://b.test/y)"
        rows = extract.extract_rows(text, set())
        self.assertEqual(len(rows), 2)
        self.assertIn('href="https://a.test/x">A</a>', rows[0])
        self.assertIn('href="https://b.test/y">B</a>', rows[1])

    def test_suffix_boundary_case_and_idn(self):
        blocked = {extract.normalize_domain("グーグル.com"), "google.com"}
        text = ("https://DRIVE.GOOGLE.COM./x https://notgoogle.com "
                "https://google.com.evil.test https://xn--qcka1pmc.com "
                "https://sub.グーグル.com")
        rows = extract.extract_rows(text, blocked)
        self.assertEqual(len(rows), 2)
        self.assertIn("<code>address=/notgoogle.com/</code>", rows[0])
        self.assertIn("<code>address=/google.com.evil.test/</code>", rows[1])

    def test_plain_text_parentheses_ports_and_ipv6(self):
        text = "(https://example.com:8443/wiki/Test_(thing)) https://[::1]/x"
        rows = extract.extract_rows(text, set())
        self.assertEqual(len(rows), 2)
        self.assertIn("<code>address=/::1/</code>", rows[0])
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
                self.assertIn("<code>address=/open.test/</code>", content)
                self.assertNotIn("<code>address=/blocked.test/</code>", content)
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
