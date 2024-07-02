## frontend/src/components/IncomeStreams.js

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  Button, 
  CircularProgress, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
    padding: theme.spacing(3),
  },
  card: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  cardContent: {
    flexGrow: 1,
  },
  title: {
    marginBottom: theme.spacing(2),
  },
  button: {
    marginTop: theme.spacing(2),
  },
  formControl: {
    marginBottom: theme.spacing(2),
    minWidth: 120,
  },
}));

const IncomeStreams = () => {
  const classes = useStyles();
  const { currentUser } = useAuth();
  const [incomeStreams, setIncomeStreams] = useState([]);
  const [availableStreams, setAvailableStreams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openInvestDialog, setOpenInvestDialog] = useState(false);
  const [selectedStream, setSelectedStream] = useState(null);
  const [investmentAmount, setInvestmentAmount] = useState('');

  useEffect(() => {
    const fetchIncomeStreams = async () => {
      try {
        const [userStreamsResponse, availableStreamsResponse] = await Promise.all([
          axios.get('/api/user-income-streams/', {
            headers: { 'Authorization': `Bearer ${currentUser.token}` },
          }),
          axios.get('/api/income-streams/', {
            headers: { 'Authorization': `Bearer ${currentUser.token}` },
          }),
        ]);
        setIncomeStreams(userStreamsResponse.data);
        setAvailableStreams(availableStreamsResponse.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch income streams. Please try again later.');
        setLoading(false);
      }
    };

    fetchIncomeStreams();
  }, [currentUser]);

  const handleInvestDialogOpen = (stream) => {
    setSelectedStream(stream);
    setOpenInvestDialog(true);
  };

  const handleInvestDialogClose = () => {
    setOpenInvestDialog(false);
    setSelectedStream(null);
    setInvestmentAmount('');
  };

  const handleInvest = async () => {
    try {
      const response = await axios.post(
        '/api/user-income-streams/',
        {
          income_stream_id: selectedStream.id,
          invested_amount: parseFloat(investmentAmount),
        },
        {
          headers: { 'Authorization': `Bearer ${currentUser.token}` },
        }
      );
      setIncomeStreams([...incomeStreams, response.data]);
      handleInvestDialogClose();
    } catch (err) {
      setError('Failed to invest. Please try again.');
    }
  };

  const handleWithdraw = async (userIncomeStreamId) => {
    try {
      await axios.post(
        `/api/user-income-streams/${userIncomeStreamId}/withdraw/`,
        {},
        {
          headers: { 'Authorization': `Bearer ${currentUser.token}` },
        }
      );
      const updatedStreams = incomeStreams.filter(stream => stream.id !== userIncomeStreamId);
      setIncomeStreams(updatedStreams);
    } catch (err) {
      setError('Failed to withdraw. Please try again.');
    }
  };

  const handleToggleAutoReinvest = async (userIncomeStreamId) => {
    try {
      const response = await axios.post(
        `/api/user-income-streams/${userIncomeStreamId}/toggle-auto-reinvest/`,
        {},
        {
          headers: { 'Authorization': `Bearer ${currentUser.token}` },
        }
      );
      const updatedStreams = incomeStreams.map(stream => 
        stream.id === userIncomeStreamId ? { ...stream, auto_reinvest: response.data.auto_reinvest } : stream
      );
      setIncomeStreams(updatedStreams);
    } catch (err) {
      setError('Failed to toggle auto-reinvest. Please try again.');
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <div className={classes.root}>
      <Typography variant="h4" className={classes.title}>
        Income Streams
      </Typography>
      <Grid container spacing={3}>
        {incomeStreams.map((stream) => (
          <Grid item xs={12} sm={6} md={4} key={stream.id}>
            <Card className={classes.card}>
              <CardContent className={classes.cardContent}>
                <Typography variant="h6">{stream.income_stream.name}</Typography>
                <Typography variant="body2">{stream.income_stream.description}</Typography>
                <Typography variant="body1">Invested: ${stream.invested_amount}</Typography>
                <Typography variant="body1">Expected Return: {stream.income_stream.expected_return}%</Typography>
                <Typography variant="body1">Auto-reinvest: {stream.auto_reinvest ? 'Yes' : 'No'}</Typography>
                <Button
                  variant="contained"
                  color="secondary"
                  className={classes.button}
                  onClick={() => handleWithdraw(stream.id)}
                >
                  Withdraw
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  className={classes.button}
                  onClick={() => handleToggleAutoReinvest(stream.id)}
                >
                  Toggle Auto-reinvest
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Typography variant="h5" className={classes.title} style={{ marginTop: '20px' }}>
        Available Income Streams
      </Typography>
      <Grid container spacing={3}>
        {availableStreams.map((stream) => (
          <Grid item xs={12} sm={6} md={4} key={stream.id}>
            <Card className={classes.card}>
              <CardContent className={classes.cardContent}>
                <Typography variant="h6">{stream.name}</Typography>
                <Typography variant="body2">{stream.description}</Typography>
                <Typography variant="body1">Minimum Investment: ${stream.min_investment}</Typography>
                <Typography variant="body1">Expected Return: {stream.expected_return}%</Typography>
                <Typography variant="body1">Risk Level: {stream.risk_level}</Typography>
                <Button
                  variant="contained"
                  color="primary"
                  className={classes.button}
                  onClick={() => handleInvestDialogOpen(stream)}
                >
                  Invest
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Dialog open={openInvestDialog} onClose={handleInvestDialogClose}>
        <DialogTitle>Invest in {selectedStream?.name}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            id="amount"
            label="Investment Amount"
            type="number"
            fullWidth
            value={investmentAmount}
            onChange={(e) => setInvestmentAmount(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleInvestDialogClose} color="primary">
            Cancel
          </Button>
          <Button onClick={handleInvest} color="primary">
            Invest
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default IncomeStreams;
