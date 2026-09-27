import re
import json
import logging
import requests
from typing import List, Dict, Any

try:
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
    HAS_YTDL = True
except ImportError:
    HAS_YTDL = False

logger = logging.getLogger(__name__)


class YouTubeScraper:
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        if HAS_YTDL:
            self.downloader = YoutubeCommentDownloader()
        else:
            self.downloader = None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

    def extract_video_id(self, url_or_id: str) -> str:
        """Extract 11-character YouTube video ID from various URL formats or raw ID."""
        if not url_or_id:
            return ""
        url_or_id = url_or_id.strip()

        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?\/]|$)',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'embed\/([0-9A-Za-z_-]{11})',
            r'shorts\/([0-9A-Za-z_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        if len(url_or_id) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', url_or_id):
            return url_or_id

        return url_or_id

    def fetch_comments(self, url: str, max_comments: int = 25) -> Dict[str, Any]:
        """
        Fetch top comments for a YouTube video URL.
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            return {
                "url": url,
                "video_id": "",
                "count": 0,
                "comments": [],
                "error": "Invalid YouTube URL or Video ID.",
                "status": "error"
            }

        full_url = f"https://www.youtube.com/watch?v={video_id}"

        # Tier 1: Try YoutubeCommentDownloader
        comments = []
        if self.downloader:
            try:
                comment_generator = self.downloader.get_comments_from_url(
                    full_url, sort_by=SORT_BY_POPULAR
                )
                for comment in comment_generator:
                    text = comment.get("text", "").strip()
                    if text:
                        comments.append(text)
                    if len(comments) >= max_comments:
                        break
            except Exception as e:
                logger.warning(f"YoutubeCommentDownloader failed for {video_id}: {e}")

        # Tier 2: Try InnerTube Direct API via requests
        if not comments:
            try:
                comments = self._scrape_m_youtube(video_id, max_comments)
            except Exception as e:
                logger.warning(f"InnerTube mobile scraping failed for {video_id}: {e}")

        # Tier 3: Sample fallback comments
        status = "success"
        if not comments:
            status = "fallback"
            comments = self._fallback_comments(video_id)[:max_comments]

        return {
            "url": url,
            "video_id": video_id,
            "count": len(comments),
            "comments": comments,
            "status": status
        }

    def _scrape_m_youtube(self, video_id: str, max_comments: int) -> List[str]:
        url = f"https://m.youtube.com/watch?v={video_id}"
        resp = self.session.get(url, timeout=self.timeout)
        if resp.status_code != 200:
            return []

        html = resp.text
        key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        token_match = re.search(r'"continuation":"([^"]+)"', html) or re.search(r'"token":"([^"]+)"', html)

        if not key_match or not token_match:
            return []

        api_key = key_match.group(1)
        curr_token = token_match.group(1)
        next_url = f"https://www.youtube.com/youtubei/v1/next?key={api_key}"

        comments = []
        while curr_token and len(comments) < max_comments:
            payload = {
                "context": {
                    "client": {
                        "clientName": "MWEB",
                        "clientVersion": "2.20240301.00.00"
                    }
                },
                "continuation": curr_token
            }
            res = self.session.post(next_url, json=payload, timeout=self.timeout)
            if res.status_code != 200:
                break
            data = res.json()

            items = []
            endpoints = data.get("onResponseReceivedEndpoints", [])
            for ep in endpoints:
                action = ep.get("appendContinuationItemsAction") or ep.get("reloadContinuationItemsCommand")
                if action:
                    items.extend(action.get("continuationItems", []))

            next_token = None
            for item in items:
                comment_thread = item.get("commentThreadRenderer")
                if comment_thread:
                    c_data = comment_thread.get("comment", {}).get("commentRenderer", {})
                    runs = c_data.get("contentText", {}).get("runs", [])
                    txt = "".join([r.get("text", "") for r in runs]).strip()
                    if txt:
                        comments.append(txt)
                continuation_item = item.get("continuationItemRenderer")
                if continuation_item:
                    cmd = continuation_item.get("continuationEndpoint", {}).get("continuationCommand", {})
                    if cmd.get("token"):
                        next_token = cmd.get("token")

            if not next_token or next_token == curr_token or len(comments) >= max_comments:
                break
            curr_token = next_token

        return comments

    def _fallback_comments(self, video_id: str) -> List[str]:
        return [
            "This video was super helpful and clearly explained! Thanks!",
            "Great explanation, everything was very clear.",
            "Honestly, I didn't find this video very informative.",
            "Amazing content as always, keep up the good work!",
            "The audio quality could be improved, but good tutorial.",
            "I watched the whole thing without getting bored.",
            "Not gonna lie, this was pretty average.",
            "Finally someone explained this topic properly!",
            "Awesome video! Subscribed!",
            "This didn't answer my questions unfortunately."
        ]
