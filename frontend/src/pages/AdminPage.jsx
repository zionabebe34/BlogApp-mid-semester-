import { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Button, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
} from '@mui/material';
import { getReports, adminDeletePost, updateReportStatus, banUser } from '../api';
import { timeAgo } from '../utils/timeAgo';

/**
 * Moderation dashboard: every open report, with the actions the requirements
 * call for — delete offending content, or ban the author.
 *
 * Note this page is only a convenience: hiding it from non-staff users is UX,
 * not security. The real gate is `@roles_required` on the backend routes.
 */
function AdminPage({ currentUser }) {
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const loadReports = () => {
    setIsLoading(true);
    getReports()
      .then(setReports)
      .catch((err) => alert(err.message))
      .finally(() => setIsLoading(false));
  };

  useEffect(loadReports, []);

  // Every action follows the same shape: call the server, then refetch the list.
  // One action can affect several rows (banning an author with three reports),
  // so refetching is safer than patching state locally.
  const runAction = async (reportId, action) => {
    setBusyId(reportId);
    try {
      await action();
      loadReports();
    } catch (err) {
      alert(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const handleDeletePost = (report) => {
    if (!window.confirm(`Delete "${report.post_title}"? This cannot be undone.`)) return;
    // Deleting the post cascades its reports away, so there is nothing left to resolve
    runAction(report.id, () => adminDeletePost(report.post_id));
  };

  const handleBanAuthor = (report) => {
    if (!window.confirm(`Ban ${report.author_name}?`)) return;
    // The post survives a ban, so the report has to be closed explicitly
    runAction(report.id, async () => {
      await banUser(report.author_id);
      await updateReportStatus(report.id, 'resolved');
    });
  };

  const handleDismiss = (report) =>
    runAction(report.id, () => updateReportStatus(report.id, 'dismissed'));

  const isAdmin = currentUser?.role === 'admin';

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" sx={{ mb: 1 }}>Moderation</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {reports.length} open report{reports.length === 1 ? '' : 's'}
      </Typography>

      {reports.length === 0 ? (
        <Typography color="text.secondary">Nothing to review right now.</Typography>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Post</TableCell>
                <TableCell>Author</TableCell>
                <TableCell>Reason</TableCell>
                <TableCell>Reported by</TableCell>
                <TableCell>When</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>{report.post_title}</TableCell>
                  <TableCell>{report.author_name}</TableCell>
                  <TableCell>{report.reason}</TableCell>
                  <TableCell>{report.reporter_name}</TableCell>
                  <TableCell>{report.created_at ? timeAgo(report.created_at) : '—'}</TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      color="error"
                      disabled={busyId === report.id}
                      onClick={() => handleDeletePost(report)}
                    >
                      Delete post
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      disabled={busyId === report.id || !isAdmin}
                      title={isAdmin ? '' : 'Only admins can ban users'}
                      onClick={() => handleBanAuthor(report)}
                    >
                      Ban author
                    </Button>
                    <Button
                      size="small"
                      disabled={busyId === report.id}
                      onClick={() => handleDismiss(report)}
                    >
                      Dismiss
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default AdminPage;
