'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { apiClient, Auction, Bid } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export default function AuctionDetailPage() {
  const { user } = useAuth();
  const params = useParams();
  const router = useRouter();
  const auctionId = parseInt(params.id as string);
  
  const [auction, setAuction] = useState<Auction | null>(null);
  const [bids, setBids] = useState<Bid[]>([]);
  const [bidAmount, setBidAmount] = useState('');
  const [loading, setLoading] = useState(true);
  const [bidLoading, setBidLoading] = useState(false);

  useEffect(() => {
    if (auctionId) {
      fetchAuctionDetails();
      fetchBids();
      
      // Set up polling for real-time updates
      const interval = setInterval(() => {
        fetchAuctionDetails();
        fetchBids();
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [auctionId]);

  const fetchAuctionDetails = async () => {
    try {
      const response = await apiClient.getAuction(auctionId);
      if (response.success) {
        setAuction(response.data?.auction || null);
      }
    } catch (error) {
      console.error('Failed to fetch auction:', error);
      toast.error('Failed to load auction details');
    } finally {
      setLoading(false);
    }
  };

  const fetchBids = async () => {
    try {
      const response = await apiClient.getAuctionBids(auctionId);
      if (response.success) {
        setBids(response.data?.bids || []);
      }
    } catch (error) {
      console.error('Failed to fetch bids:', error);
    }
  };

  const handleBidSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!user) {
      toast.error('Please log in to place a bid');
      router.push('/login');
      return;
    }

    if (!auction) return;

    const amount = parseFloat(bidAmount);
    if (isNaN(amount) || amount <= auction.current_price) {
      toast.error(`Bid must be higher than current price: $${auction.current_price}`);
      return;
    }

    setBidLoading(true);

    try {
      const response = await apiClient.placeBid({
        auction_id: auctionId,
        amount: amount
      });

      if (response.success) {
        toast.success('Bid placed successfully!');
        setBidAmount('');
        // Refresh data
        await fetchAuctionDetails();
        await fetchBids();
      } else {
        toast.error(response.message || 'Failed to place bid');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to place bid');
    } finally {
      setBidLoading(false);
    }
  };

  const updateAuctionStatus = async (newStatus: string) => {
    try {
      const response = await apiClient.patch(`/auctions/${auctionId}/status?new_status=${newStatus}`);
      if (response.success) {
        toast.success(`Auction status updated to ${newStatus}`);
        await fetchAuctionDetails();
      } else {
        toast.error(response.message || 'Failed to update status');
      }
    } catch (error) {
      console.error('Status update error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to update status');
    }
  };

  const autoUpdateStatuses = async () => {
    try {
      const response = await apiClient.get('/auctions/manage/auto-update-status');
      if (response.success) {
        toast.success('Auction statuses updated automatically');
        await fetchAuctionDetails();
      } else {
        toast.error(response.message || 'Failed to auto-update');
      }
    } catch (error) {
      console.error('Auto-update error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to auto-update');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live':
        return 'bg-green-500 hover:bg-green-600';
      case 'pending':
        return 'bg-yellow-500 hover:bg-yellow-600';
      case 'ended':
        return 'bg-gray-500 hover:bg-gray-600';
      default:
        return 'bg-gray-500 hover:bg-gray-600';
    }
  };

  const getTimeRemaining = (endsAt: string) => {
    const now = new Date();
    const endTime = new Date(endsAt);
    const diff = endTime.getTime() - now.getTime();

    if (diff <= 0) return 'Ended';

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const isOwnAuction = user && auction && user.id === auction.owner_id;
  const canBid = user && auction && auction.status === 'live' && !isOwnAuction;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="text-center">
            <p className="text-gray-500">Loading auction details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!auction) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="text-center">
            <p className="text-gray-500 mb-4">Auction not found</p>
            <Button onClick={() => router.push('/auctions')}>
              Back to Auctions
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Auction Details */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-2xl">{auction.title}</CardTitle>
                    <CardDescription className="mt-2">
                      {auction.description}
                    </CardDescription>
                  </div>
                  <Badge className={getStatusColor(auction.status)}>
                    {auction.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-3">Auction Details</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Starting Price:</span>
                        <span className="font-semibold">${auction.starting_price}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Current Price:</span>
                        <span className="font-semibold text-green-600 text-lg">
                          ${auction.current_price}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Time Remaining:</span>
                        <span className="font-semibold">
                          {getTimeRemaining(auction.ends_at)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">End Date:</span>
                        <span className="text-gray-700">
                          {new Date(auction.ends_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Bidding Section */}
                  <div>
                    <h3 className="font-semibold mb-3">Place Bid</h3>
                    {canBid ? (
                      <form onSubmit={handleBidSubmit} className="space-y-4">
                        <div>
                          <Label htmlFor="bidAmount">Your Bid ($)</Label>
                          <Input
                            id="bidAmount"
                            type="number"
                            step="0.01"
                            min={auction.current_price + 0.01}
                            value={bidAmount}
                            onChange={(e) => setBidAmount(e.target.value)}
                            placeholder={`Minimum: $${(auction.current_price + 0.01).toFixed(2)}`}
                            required
                          />
                        </div>
                        <Button 
                          type="submit" 
                          className="w-full"
                          disabled={bidLoading}
                        >
                          {bidLoading ? 'Placing Bid...' : 'Place Bid'}
                        </Button>
                      </form>
                    ) : (
                      <div className="text-center py-4">
                        {!user ? (
                          <p className="text-gray-600 mb-4">
                            Please log in to place a bid
                          </p>
                        ) : isOwnAuction ? (
                          <p className="text-gray-600">
                            You cannot bid on your own auction
                          </p>
                        ) : auction.status === 'ended' ? (
                          <p className="text-gray-600">
                            This auction has ended
                          </p>
                        ) : auction.status === 'pending' ? (
                          <p className="text-gray-600">
                            This auction hasn't started yet
                          </p>
                        ) : null}
                        
                        {!user && (
                          <Button onClick={() => router.push('/login')}>
                            Login to Bid
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Bid History */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Bid History</CardTitle>
                <CardDescription>
                  {bids.length} bid{bids.length !== 1 ? 's' : ''} placed
                </CardDescription>
              </CardHeader>
              <CardContent>
                {bids.length > 0 ? (
                  <div className="space-y-4">
                    {bids.map((bid, index) => (
                      <div key={bid.id}>
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-semibold">${bid.amount}</p>
                            <p className="text-sm text-gray-600">
                              {new Date(bid.timestamp).toLocaleString()}
                            </p>
                          </div>
                          {index === 0 && (
                            <Badge variant="secondary">Highest</Badge>
                          )}
                        </div>
                        {index < bids.length - 1 && (
                          <Separator className="mt-4" />
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">
                    No bids yet. Be the first to bid!
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Admin Controls - Only show if user is auction creator */}
        {auction.creator_id === user?.user_id && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Admin Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Button
                  onClick={() => updateAuctionStatus('live')}
                  disabled={auction.status === 'live' || auction.status === 'ended'}
                  variant="outline"
                  size="sm"
                >
                  Make Live
                </Button>
                <Button
                  onClick={() => updateAuctionStatus('ended')}
                  disabled={auction.status === 'ended'}
                  variant="outline"
                  size="sm"
                >
                  End Auction
                </Button>
                <Button
                  onClick={autoUpdateStatuses}
                  variant="outline"
                  size="sm"
                >
                  Auto-Update All
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Current status: <span className="font-medium">{auction.status}</span>
              </p>
            </CardContent>
          </Card>
        )}

        <div className="mt-8 text-center">
          <Button variant="outline" onClick={() => router.push('/auctions')}>
            ← Back to Auctions
          </Button>
        </div>
      </main>
    </div>
  );
} 