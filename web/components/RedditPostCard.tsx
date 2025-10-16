'use client'

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp, ExternalLink, MessageSquare, ArrowBigUp } from "lucide-react";
import { RedditPost } from "@/lib/api";
import { ImageCarousel } from "@/components/ImageCarousel";

interface RedditPostCardProps {
  post: RedditPost;
}

export function RedditPostCard({ post }: RedditPostCardProps) {
  const [expanded, setExpanded] = useState(false);

  // Format the subreddit name
  const subredditDisplay = `r/${post.subreddit}`;

  // Truncate long text for preview
  const truncateText = (text: string, maxLength: number = 200) => {
    if (!text || text === '[No text content]') return text;
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const hasComments = post.comments && post.comments.length > 0;

  return (
    <Card className="bg-white border-gray-200 hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="space-y-2">
          {/* Subreddit badge and metadata */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                {subredditDisplay}
              </span>
              <span className="text-sm text-gray-500">
                by u/{post.author}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <ArrowBigUp className="h-4 w-4 text-orange-500" />
                {post.score.toLocaleString()}
              </span>
              <span>{post.date}</span>
            </div>
          </div>

          {/* Post title */}
          <CardTitle className="text-lg text-gray-900 leading-tight">
            {post.title}
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Post content */}
        {post.text && post.text !== '[No text content]' && (
          <div className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
            {truncateText(post.text, 300)}
          </div>
        )}

        {/* Post images */}
        {post.image_urls && post.image_urls.length > 0 && (
          <ImageCarousel 
            images={post.image_urls} 
            alt={post.title}
            maxHeight="500px"
          />
        )}

        {/* Link to original post */}
        <div className="pt-2 border-t border-gray-100">
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-orange-600 hover:text-orange-700 hover:underline"
          >
            View on Reddit
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>

        {/* Comments section */}
        {hasComments && (
          <div className="pt-2 border-t border-gray-100">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 w-full"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Top {post.comments.length} Comments</span>
              {expanded ? (
                <ChevronUp className="h-4 w-4 ml-auto" />
              ) : (
                <ChevronDown className="h-4 w-4 ml-auto" />
              )}
            </button>

            {expanded && (
              <div className="mt-3 space-y-3">
                {post.comments.map((comment, idx) => (
                  <div
                    key={idx}
                    className="pl-4 border-l-2 border-orange-200 space-y-1"
                  >
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="font-medium">u/{comment.author}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <ArrowBigUp className="h-3 w-3" />
                        {comment.score}
                      </span>
                      <span>•</span>
                      <span>{comment.date}</span>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {truncateText(comment.text, 400)}
                    </p>
                    {/* Comment images */}
                    {comment.image_urls && comment.image_urls.length > 0 && (
                      <div className="mt-2">
                        <ImageCarousel 
                          images={comment.image_urls} 
                          alt="Comment image"
                          maxHeight="300px"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
