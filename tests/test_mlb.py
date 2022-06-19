def test_twitter_live():
    with open('./mlb/automated.py') as f:
        numPostTweet = 0
        for line in f.readlines():
            if 'postTweet' in line and 'import' not in line:
                print(line)
                numPostTweet += 1
                assert '#' not in line, f'The following line may be commented: {line}'
        assert numPostTweet > 0, 'no attempt to tweet'
