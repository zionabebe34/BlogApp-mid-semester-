import React, { useState, useEffect } from 'react';
import DOMPurify from 'dompurify';
import {
  Card, CardContent, Box, Typography, Avatar,
  Dialog, DialogTitle, DialogContent, TextField, Button, Divider,
} from '@mui/material';
import { timeAgo } from '../utils/timeAgo';
import { likePost, unlikePost, getPostLikes, getPostComments, addComment } from '../api';

/**
 * Instagram-like square tile: dominant square image with an overlay
 * showing author, time and a short title/caption.
 */
function SinglePostCard({ postId, title, authorName, authorEmail, body, imageUrl, createdAt, profilePictureUrl }) {
  const author = authorName || authorEmail || 'Unknown';
  const hasImage = Boolean(imageUrl);

  const [likeCount, setLikeCount] = useState(0);
  const [likedByMe, setLikedByMe] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentsOpen, setCommentsOpen] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Fetch this post's like + comment info once, when the card mounts
  useEffect(() => {
    if (!postId) return;
    getPostLikes(postId)
      .then((data) => {
        setLikeCount(data.like_count);
        setLikedByMe(data.liked_by_me);
      })
      .catch(() => {}); // a failed like-count fetch shouldn't break the card

    getPostComments(postId).then(setComments).catch(() => {});
  }, [postId]);

  // Flip the like state locally so the UI reacts instantly (same idea as follow/unfollow)
  const handleLikeToggle = async (event) => {
    event.stopPropagation();
    try {
      if (likedByMe) {
        await unlikePost(postId);
        setLikedByMe(false);
        setLikeCount((prev) => prev - 1);
      } else {
        await likePost(postId);
        setLikedByMe(true);
        setLikeCount((prev) => prev + 1);
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAddComment = async () => {
    const text = newComment.trim();
    if (!text) return;

    setIsSending(true);
    try {
      await addComment(postId, text);
      setNewComment('');
      // The backend only returns a confirmation message, not the new comment
      // object — so we refetch the list to get it with its id, author and time.
      const fresh = await getPostComments(postId);
      setComments(fresh);
    } catch (err) {
      alert(err.message);
    } finally {
      setIsSending(false);
    }
  };

  // Defined once, rendered in both layouts below
  const likeButton = (
    <Box
      onClick={handleLikeToggle}
      sx={{ display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer', userSelect: 'none' }}
    >
      <Typography component="span" sx={{ fontSize: 18, lineHeight: 1, color: likedByMe ? '#e0245e' : 'inherit' }}>
        {likedByMe ? '♥' : '♡'}
      </Typography>
      <Typography variant="caption">{likeCount}</Typography>
    </Box>
  );

  const commentButton = (
    <Box
      onClick={(event) => {
        event.stopPropagation();
        setCommentsOpen(true);
      }}
      sx={{ display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer', userSelect: 'none' }}
    >
      <Typography component="span" sx={{ fontSize: 15, lineHeight: 1 }}>💬</Typography>
      <Typography variant="caption">{comments.length}</Typography>
    </Box>
  );

  // Like + comment side by side — rendered in both layouts below
  const actionsRow = (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {likeButton}
      {commentButton}
    </Box>
  );

  const commentsDialog = (
    <Dialog
      open={commentsOpen}
      onClose={() => setCommentsOpen(false)}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle sx={{ fontSize: '1rem' }}>Comments</DialogTitle>

      <DialogContent dividers>
        {comments.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No comments yet.
          </Typography>
        )}

        {comments.map((comment) => (
          <Box key={comment.id} sx={{ display: 'flex', gap: 1.5, mb: 2 }}>
            <Avatar src={comment.profile_picture_url} sx={{ width: 32, height: 32 }}>
              {comment.user_name?.[0]?.toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {comment.user_name}
                {comment.created_at && (
                  <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                    · {timeAgo(comment.created_at)}
                  </Typography>
                )}
              </Typography>
              <Typography variant="body2">{comment.content}</Typography>
            </Box>
          </Box>
        ))}

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Write a comment…"
            value={newComment}
            onChange={(event) => setNewComment(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') handleAddComment();
            }}
          />
          <Button
            variant="contained"
            onClick={handleAddComment}
            disabled={isSending || !newComment.trim()}
          >
            Post
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );

  if (!hasImage) {
    // Compact layout for text-only posts
    return (
      <>
      <Card sx={{ overflow: 'hidden', borderRadius: 2, cursor: 'pointer' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Avatar src={profilePictureUrl} sx={{ width: 34, height: 34 }}>
              {author[0]?.toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {author}
              </Typography>
              {createdAt && (
                <Typography variant="caption" color="text.secondary">
                  · {timeAgo(createdAt)}
                </Typography>
              )}
            </Box>
          </Box>

          <Typography variant="h6" sx={{ mb: 1, fontSize: '1.03rem' }}>{title}</Typography>

          <Typography variant="body2" color="text.secondary" sx={{ maxHeight: 84, overflow: 'hidden' }} dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(body || '') }} />

          <Box sx={{ mt: 1.5 }}>{actionsRow}</Box>
        </CardContent>
      </Card>
      {commentsDialog}
      </>
    );
  }

  // Image-present layout (medium rectangular tile: larger than text-only, but not huge)
  return (
    <>
    <Card sx={{ overflow: 'hidden', borderRadius: 2, cursor: 'pointer' }}>
      <Box sx={{ position: 'relative' }}>
        <Box
          sx={{
            width: '100%',
            aspectRatio: '16 / 9',
            maxHeight: { xs: 320, md: 420 },
            backgroundImage: imageUrl ? `url(${imageUrl})` : 'linear-gradient(90deg,#eee,#ddd)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        />

        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            background: 'linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.55) 100%)',
            color: 'white',
            p: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar src={profilePictureUrl} sx={{ width: 30, height: 30 }} />
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {author}
            </Typography>
            {createdAt && (
              <Typography variant="caption" sx={{ ml: 1, opacity: 0.9 }}>
                · {timeAgo(createdAt)}
              </Typography>
            )}
          </Box>

          <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 500, maxWidth: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {title}
          </Typography>

          <Typography variant="caption" sx={{ mt: 0.5, color: 'rgba(255,255,255,0.9)', display: 'block' }}>
            <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize((body || '').slice(0, 120)) }} />
            {body && body.length > 120 ? '…' : ''}
          </Typography>

          <Box sx={{ mt: 1 }}>{actionsRow}</Box>
        </Box>
      </Box>
    </Card>
    {commentsDialog}
    </>
  );
}

export default SinglePostCard;
