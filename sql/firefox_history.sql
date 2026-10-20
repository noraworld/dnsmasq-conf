-- https://chatgpt.com/c/6ad4e7f8-4440-83e8-ba7d-ca5956527d0b

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
