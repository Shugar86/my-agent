try:
    import tweepy
except ImportError:
    tweepy = None


def _validate_creds(api_key, api_secret, access_token, access_secret):
    if not all([api_key, api_secret, access_token, access_secret]):
        return {"error": "Twitter credentials missing. Provide api_key, api_secret, access_token, access_secret."}
    return None


def post_tweet(api_key: str, api_secret: str, access_token: str, access_secret: str,
               text: str) -> dict:
    from core.validation import validate_twitter_text_or_error
    if tweepy is None:
        return {"error": "tweepy not installed"}
    err = _validate_creds(api_key, api_secret, access_token, access_secret)
    if err:
        return err
    err = validate_twitter_text_or_error(text)
    if err:
        return {"error": err}
    try:
        client = tweepy.Client(
            consumer_key=api_key, consumer_secret=api_secret,
            access_token=access_token, access_token_secret=access_secret,
        )
        resp = client.create_tweet(text=text)
        return {"success": True, "id": resp.data["id"], "text": text}
    except Exception as e:
        return {"error": str(e)}


def search_tweets(api_key: str, api_secret: str, access_token: str, access_secret: str,
                  query: str, max_results: int = 10) -> dict:
    from core.validation import validate_not_empty_or_error
    if tweepy is None:
        return {"error": "tweepy not installed"}
    err = _validate_creds(api_key, api_secret, access_token, access_secret)
    if err:
        return err
    err = validate_not_empty_or_error(query, "query")
    if err:
        return {"error": err}
    try:
        client = tweepy.Client(
            consumer_key=api_key, consumer_secret=api_secret,
            access_token=access_token, access_token_secret=access_secret,
        )
        resp = client.search_recent_tweets(query=query, max_results=max_results)
        tweets = [{"id": t.id, "text": t.text, "created_at": str(t.created_at)}
                  for t in (resp.data or [])]
        return {"tweets": tweets, "count": len(tweets)}
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="post_tweet",
        description="Post a tweet to Twitter/X. Max 280 characters.",
        parameters={"type": "object", "properties": {
            "api_key": {"type": "string"},
            "api_secret": {"type": "string"},
            "access_token": {"type": "string"},
            "access_secret": {"type": "string"},
            "text": {"type": "string"},
        }},
        execute_fn=lambda api_key="", api_secret="", access_token="", access_secret="", text="":
            post_tweet(api_key, api_secret, access_token, access_secret, text),
    )
    registry.register(
        name="search_tweets",
        description="Search recent tweets on Twitter/X by query.",
        parameters={"type": "object", "properties": {
            "api_key": {"type": "string"},
            "api_secret": {"type": "string"},
            "access_token": {"type": "string"},
            "access_secret": {"type": "string"},
            "query": {"type": "string"},
            "max_results": {"type": "integer"},
        }},
        execute_fn=lambda api_key="", api_secret="", access_token="", access_secret="",
                      query="", max_results=10:
            search_tweets(api_key, api_secret, access_token, access_secret, query, max_results),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["post_tweet", "search_tweets"]:
        registry.unregister(name)
