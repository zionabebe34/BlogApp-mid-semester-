import React from 'react';
import { Card, CardContent, CardMedia, Typography, Box, Avatar } from '@mui/material';
import { timeAgo } from '../utils/timeAgo';

function SinglePostCard({ title, authorName, authorEmail, body, imageUrl, createdAt, profilePictureUrl }) {
  // Expand to full content while the mouse is over the card.
  const [expanded, setExpanded] = React.useState(false);

  return (
    <Card
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      sx={{
        maxWidth: 420,
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        transition: 'box-shadow 0.2s ease',
        // Lift the expanded card above its neighbors so it overlays instead of
        // pushing the grid around.
        zIndex: expanded ? 5 : 1,
        boxShadow: expanded ? 8 : 1,
      }}
    >
      {imageUrl && (
        <CardMedia component="img" height="180" image={imageUrl} alt={title} sx={{ objectFit: 'cover' }} />
      )}
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6">{title}</Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          {profilePictureUrl && <Avatar src={profilePictureUrl} sx={{ width: 24, height: 24 }} />}
          <Typography variant="body2" color="text.secondary">
            {authorName || authorEmail || 'Unknown'}
            {createdAt && <> · {timeAgo(createdAt)}</>}
          </Typography>
        </Box>

        <Box
          sx={{
            transition: 'max-height 0.25s ease',
            ...(expanded ? { maxHeight: 1000, overflow: 'visible' } : { maxHeight: 90, overflow: 'hidden' }),
            '& a': { color: '#5b6dfa' },
            '& img': { maxWidth: '100%' },
          }}
          dangerouslySetInnerHTML={{ __html: body || '' }}
        />
      </CardContent>
    </Card>
  );
}

export default SinglePostCard;
