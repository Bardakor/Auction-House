'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiClient, Auction } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export default function AuctionsPage() {
  const { user } = useAuth();
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [filteredAuctions, setFilteredAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    fetchAuctions();
  }, []);

  useEffect(() => {
    filterAuctions();
  }, [auctions, searchTerm, statusFilter]);

  const fetchAuctions = async () => {
    try {
      const response = await apiClient.getAuctions();
      if (response.success) {
        setAuctions(response.data?.auctions || []);
      }
    } catch (error) {
      toast.error('Failed to fetch auctions');
      console.error('Failed to fetch auctions:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAuctions = () => {
    let filtered = auctions;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(
        (auction) =>
          auction.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          auction.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter((auction) => auction.status === statusFilter);
    }

    setFilteredAuctions(filtered);
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

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Auctions</h1>
          {user && (
            <Link href="/create-auction">
              <Button>Create Auction</Button>
            </Link>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1">
            <Input
              placeholder="Search auctions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              onClick={() => setStatusFilter('all')}
            >
              All
            </Button>
            <Button
              variant={statusFilter === 'live' ? 'default' : 'outline'}
              onClick={() => setStatusFilter('live')}
            >
              Live
            </Button>
            <Button
              variant={statusFilter === 'pending' ? 'default' : 'outline'}
              onClick={() => setStatusFilter('pending')}
            >
              Upcoming
            </Button>
            <Button
              variant={statusFilter === 'ended' ? 'default' : 'outline'}
              onClick={() => setStatusFilter('ended')}
            >
              Ended
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading auctions...</p>
          </div>
        ) : filteredAuctions.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAuctions.map((auction) => (
              <Card key={auction.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg line-clamp-2">{auction.title}</CardTitle>
                    <Badge className={getStatusColor(auction.status)}>
                      {auction.status}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-3">
                    {auction.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Starting Price:</span>
                      <span className="font-semibold">${auction.starting_price}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Current Price:</span>
                      <span className="font-semibold text-green-600">${auction.current_price}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Time Remaining:</span>
                      <span className="font-semibold">{getTimeRemaining(auction.ends_at)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Ends:</span>
                      <span className="text-gray-700">
                        {new Date(auction.ends_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <Link href={`/auctions/${auction.id}`} className="block mt-4">
                    <Button className="w-full">
                      {auction.status === 'live' ? 'Place Bid' : 'View Details'}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">
              {searchTerm || statusFilter !== 'all' 
                ? 'No auctions match your filters.' 
                : 'No auctions available yet.'
              }
            </p>
            {user && !searchTerm && statusFilter === 'all' && (
              <Link href="/create-auction">
                <Button>Create the First Auction</Button>
              </Link>
            )}
          </div>
        )}
      </main>
    </div>
  );
} 