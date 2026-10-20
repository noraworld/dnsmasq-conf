-- Overview
--   Export Firefox history in Markdown style
--
-- Format:
--   [Google](<https://www.google.com>)
--   [Yahoo!](<https://www.yahoo.co.jp>)
--
-- Usage:
--   $ cd sql
--   $ cp -i $HOME/Library/Application\ Support/Firefox/Profiles/*.default-release/places.sqlite places_$(date '+%Y%m%d%H%M%S').sqlite
--   $ sqlite3 -noheader places_*.sqlite < firefox_history.sql > history.md
--   $ head history.md
--
--   $ rm history.md places_*.sqlite*     # when you want to reset
--
-- Reference:
--   https://chatgpt.com/c/6ad4e7f8-4440-83e8-ba7d-ca5956527d0b
--

SELECT
  '* [' ||
  REPLACE(
    REPLACE(
      REPLACE(
        COALESCE(title, ''),
        char(92), char(92) || char(92)
      ),
      '[', char(92) || '['
    ),
    ']', char(92) || ']'
  ) ||
  '](<' ||
  REPLACE(url, '>', '%3E') ||
  '>)'
FROM moz_places
WHERE url IS NOT NULL
ORDER BY id;
