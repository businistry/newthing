## frontend/src/components/Dashboard.js

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Typography, Card, CardContent, Grid, Button, CircularProgress } from '@material-ui/core';
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
}));

const Dashboard = () => {
  const classes = useStyles();
  const { currentUser } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    totalInvestments: 0,
    totalEarnings: 0,
    overallRoi: 0,
    activeIncomeStreams: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await axios.get('/api/analytics/overview/', {
          headers: {
            'Authorization': `Bearer ${currentUser.token}`,
          },
        });
        setDashboardData(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch dashboard data. Please try again later.');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [currentUser]);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <div className={classes.root}>
      <Typography variant="h4" className={classes.title}>
        Welcome, {currentUser.username}!
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Total Investments</Typography>
              <Typography variant="h4">${dashboardData.totalInvestments.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Total Earnings</Typography>
              <Typography variant="h4">${dashboardData.totalEarnings.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Overall ROI</Typography>
              <Typography variant="h4">{dashboardData.overallRoi.toFixed(2)}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Active Income Streams</Typography>
              <Typography variant="h4">{dashboardData.activeIncomeStreams}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      <Grid container spacing={3} style={{ marginTop: '20px' }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Income Streams</Typography>
              <Typography variant="body1">Manage your active income streams and explore new opportunities.</Typography>
              <Button
                component={Link}
                to="/income-streams"
                variant="contained"
                color="primary"
                className={classes.button}
              >
                View Income Streams
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Analytics</Typography>
              <Typography variant="body1">Dive deep into your investment performance and financial analytics.</Typography>
              <Button
                component={Link}
                to="/analytics"
                variant="contained"
                color="primary"
                className={classes.button}
              >
                View Analytics
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card className={classes.card}>
            <CardContent className={classes.cardContent}>
              <Typography variant="h6">Education</Typography>
              <Typography variant="body1">Access educational resources to improve your investment knowledge.</Typography>
              <Button
                component={Link}
                to="/education"
                variant="contained"
                color="primary"
                className={classes.button}
              >
                Explore Education
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard;
