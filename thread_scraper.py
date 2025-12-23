#!/usr/bin/env python3
"""
Complete Reddit Thread Scraper using PRAW
Fetches ALL comments including nested replies and "more" children

Setup:
1. Install PRAW: pip install praw
2. Create a Reddit app at: https://www.reddit.com/prefs/apps
   - Click "create another app..."
   - Choose "script"
   - Set redirect URI to: http://localhost:8080
3. Fill in your credentials below
"""

import praw
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import sys

class RedditThreadScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """
        Initialize Reddit API client
        
        Args:
            client_id: Your Reddit app's client ID
            client_secret: Your Reddit app's client secret
            user_agent: Your app's user agent string
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.all_comments = []
        self.comment_count = 0
        
    def extract_comment_data(self, comment) -> Dict[str, Any]:
        """Extract relevant data from a comment object"""
        return {
            'id': comment.id,
            'author': str(comment.author) if comment.author else '[deleted]',
            'body': comment.body,
            'score': comment.score,
            'created_utc': comment.created_utc,
            'created_datetime': datetime.fromtimestamp(comment.created_utc).isoformat(),
            'permalink': comment.permalink,
            'parent_id': comment.parent_id,
            'depth': comment.depth if hasattr(comment, 'depth') else 0,
            'is_submitter': comment.is_submitter,
            'distinguished': comment.distinguished,
            'edited': bool(comment.edited),
            'controversiality': comment.controversiality,
            'gilded': comment.gilded,
        }
    
    def process_comment_tree(self, comment, depth: int = 0) -> List[Dict]:
        """
        Recursively process a comment and all its replies
        
        Args:
            comment: PRAW comment object
            depth: Current nesting depth
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        # Extract current comment
        comment_data = self.extract_comment_data(comment)
        comment_data['depth'] = depth
        comments.append(comment_data)
        self.comment_count += 1
        
        if self.comment_count % 50 == 0:
            print(f"  Processed {self.comment_count} comments...", end='\r')
        
        # Process replies recursively
        try:
            # Replace MoreComments objects with actual comments
            comment.replies.replace_more(limit=None)
            
            for reply in comment.replies:
                comments.extend(self.process_comment_tree(reply, depth + 1))
        except Exception as e:
            print(f"\n  Warning: Error processing replies for comment {comment.id}: {e}")
        
        return comments
    
    def scrape_submission(self, submission_id: str) -> Dict[str, Any]:
        """
        Scrape a complete Reddit submission/thread
        
        Args:
            submission_id: The Reddit post ID
            
        Returns:
            Dictionary with post data and all comments
        """
        print("=" * 80)
        print("Reddit Thread Scraper (PRAW)")
        print("=" * 80)
        print(f"\nFetching submission: {submission_id}")
        
        # Get the submission
        submission = self.reddit.submission(id=submission_id)
        
        # Extract post data
        post_data = {
            'id': submission.id,
            'title': submission.title,
            'author': str(submission.author) if submission.author else '[deleted]',
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'created_utc': submission.created_utc,
            'created_datetime': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'url': submission.url,
            'selftext': submission.selftext,
            'permalink': submission.permalink,
            'subreddit': str(submission.subreddit),
            'link_flair_text': submission.link_flair_text,
            'over_18': submission.over_18,
            'spoiler': submission.spoiler,
            'locked': submission.locked,
            'gilded': submission.gilded,
        }
        
        print(f"\n📝 Title: {post_data['title']}")
        print(f"👤 Author: u/{post_data['author']}")
        print(f"⬆️  Score: {post_data['score']} ({post_data['upvote_ratio']*100:.1f}% upvoted)")
        print(f"💬 Comments: {post_data['num_comments']}")
        print(f"📅 Posted: {post_data['created_datetime']}")
        
        # Process all comments
        print(f"\n🔍 Fetching all comments (this may take a while)...")
        print("   This includes all nested replies and 'more' children...")
        
        self.comment_count = 0
        self.all_comments = []
        
        # Replace all MoreComments objects with actual comments
        print("   Expanding 'more comments' objects...")
        submission.comments.replace_more(limit=None)
        print(f"   Found {len(submission.comments.list())} total comments")
        
        # Process top-level comments and their trees
        print("   Processing comment trees...")
        for comment in submission.comments:
            self.all_comments.extend(self.process_comment_tree(comment, depth=0))
        
        print(f"\n✓ Successfully extracted {len(self.all_comments)} comments!")
        
        return {
            'post': post_data,
            'comments': self.all_comments,
            'total_comments': len(self.all_comments),
            'scraped_at': datetime.now().isoformat(),
        }
    
    def save_results(self, results: Dict, output_prefix: str = "reddit_complete"):
        """Save results to multiple file formats"""
        
        # JSON (complete data)
        json_file = f"{output_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved complete JSON to: {json_file}")
        
        # Readable text file
        txt_file = f"{output_prefix}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            post = results['post']
            
            f.write("=" * 80 + "\n")
            f.write(f"TITLE: {post['title']}\n")
            f.write(f"AUTHOR: u/{post['author']}\n")
            f.write(f"SUBREDDIT: r/{post['subreddit']}\n")
            f.write(f"SCORE: {post['score']} ({post['upvote_ratio']*100:.1f}% upvoted)\n")
            f.write(f"URL: {post['url']}\n")
            f.write(f"POSTED: {post['created_datetime']}\n")
            f.write(f"COMMENTS: {post['num_comments']}\n")
            f.write(f"PERMALINK: https://reddit.com{post['permalink']}\n")
            f.write("=" * 80 + "\n\n")
            
            if post['selftext']:
                f.write(f"{post['selftext']}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write(f"COMMENTS ({len(results['comments'])} total)\n")
            f.write("-" * 80 + "\n\n")
            
            for comment in results['comments']:
                indent = "  " * comment['depth']
                
                # Header
                f.write(f"{indent}┌─ [{comment['score']}] u/{comment['author']}")
                if comment['is_submitter']:
                    f.write(" [OP]")
                if comment['distinguished']:
                    f.write(f" [{comment['distinguished']}]")
                f.write(f" (depth: {comment['depth']})\n")
                
                # Body
                for line in comment['body'].split('\n'):
                    f.write(f"{indent}│  {line}\n")
                
                # Footer
                f.write(f"{indent}│  [ID: {comment['id']}]\n")
                f.write(f"{indent}└─\n\n")
        
        print(f"✓ Saved readable text to: {txt_file}")
        
        # CSV (for easy filtering/analysis)
        csv_file = f"{output_prefix}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("id,author,score,depth,is_submitter,created_datetime,body\n")
            for c in results['comments']:
                body = c['body'].replace('"', '""').replace('\n', ' ')
                author = c['author'].replace('"', '""')
                f.write(f'"{c["id"]}","{author}",{c["score"]},{c["depth"]},')
                f.write(f'{c["is_submitter"]},"{c["created_datetime"]}","{body}"\n')
        
        print(f"✓ Saved CSV to: {csv_file}")
        
        # Top comments summary
        summary_file = f"{output_prefix}_top_comments.txt"
        sorted_comments = sorted(results['comments'], key=lambda x: x['score'], reverse=True)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("TOP 50 COMMENTS BY SCORE\n")
            f.write("=" * 80 + "\n\n")
            
            for i, comment in enumerate(sorted_comments[:50], 1):
                f.write(f"{i}. u/{comment['author']} (Score: {comment['score']}, Depth: {comment['depth']})\n")
                f.write(f"   {comment['body'][:500]}\n")
                f.write(f"   https://reddit.com{comment['permalink']}\n")
                f.write("-" * 80 + "\n\n")
        
        print(f"✓ Saved top comments to: {summary_file}")
    
    def search_user(self, results: Dict, username: str) -> List[Dict]:
        """Search for all comments by a specific user"""
        return [c for c in results['comments'] 
                if c['author'].lower() == username.lower()]


def main():
    """
    Main execution function
    
    YOU NEED TO FILL IN YOUR REDDIT API CREDENTIALS BELOW
    """
    
    # ========================================================================
    # REDDIT API CREDENTIALS - FILL THESE IN!
    # ========================================================================
    # Get these from: https://www.reddit.com/prefs/apps
    
    CLIENT_ID = "YOUR_CLIENT_ID_HERE"          # The string under "personal use script"
    CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"   # The "secret" field
    USER_AGENT = "python:reddit_scraper:v1.0 (by /u/YOUR_USERNAME)"
    
    # ========================================================================
    
    # The thread to scrape
    SUBMISSION_ID = "1ptvi51"  # From the URL: /comments/1ptvi51/
    
    # Output location
    OUTPUT_PREFIX = "reddit_complete"
    
    # ========================================================================
    
    # Validate credentials
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE" or CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
        print("ERROR: You need to fill in your Reddit API credentials!")
        print("\nFollow these steps:")
        print("1. Go to: https://www.reddit.com/prefs/apps")
        print("2. Click 'create another app...' at the bottom")
        print("3. Fill in:")
        print("   - name: anything (e.g., 'reddit_scraper')")
        print("   - Choose 'script'")
        print("   - redirect uri: http://localhost:8080")
        print("4. Click 'create app'")
        print("5. Copy the client_id (string under 'personal use script')")
        print("6. Copy the secret")
        print("7. Paste them into this script")
        sys.exit(1)
    
    # Initialize scraper
    print("Initializing Reddit API client...")
    scraper = RedditThreadScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Scrape the thread
    print("Starting scrape...")
    results = scraper.scrape_submission(SUBMISSION_ID)
    
    # Save results
    print("\nSaving results...")
    scraper.save_results(results, OUTPUT_PREFIX)
    
    # Search for specific user
    print("\n" + "=" * 80)
    print("SEARCHING FOR 'boredlibertine'")
    print("=" * 80)
    
    user_comments = scraper.search_user(results, 'boredlibertine')
    
    if user_comments:
        print(f"\n✓ Found {len(user_comments)} comment(s) by u/boredlibertine:\n")
        for i, comment in enumerate(user_comments, 1):
            print(f"\nComment #{i}")
            print(f"Score: {comment['score']} | Depth: {comment['depth']}")
            print(f"Posted: {comment['created_datetime']}")
            print(f"Link: https://reddit.com{comment['permalink']}")
            print(f"\n{comment['body']}\n")
            print("-" * 80)
    else:
        print("\n❌ No comments by u/boredlibertine found")
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)
    print(f"Total comments scraped: {results['total_comments']}")
    print(f"Expected comments: {results['post']['num_comments']}")
    if results['total_comments'] >= results['post']['num_comments']:
        print("✓ Successfully retrieved ALL comments!")
    else:
        print(f"Note: Some comments may have been deleted/removed")


if __name__ == "__main__":
    main()
