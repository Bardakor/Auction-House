'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ClientOnly } from '@/components/ClientOnly';
import { apiClient, Auction } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function HomePage() {
  const { user } = useAuth();
  const [recentAuctions, setRecentAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecentAuctions = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await apiClient.getAuctions();
      if (response.success) {
        setRecentAuctions(response.data?.auctions?.slice(0, 6) || []);
      } else {
        setError('Failed to load auctions');
      }
    } catch (error) {
      console.error('Failed to fetch auctions:', error);
      setError('Unable to connect to the server. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Add a small delay to ensure services are ready
    const timer = setTimeout(() => {
      fetchRecentAuctions();
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live':
        return 'bg-green-500';
      case 'pending':
        return 'bg-yellow-500';
      case 'ended':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Auction Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Discover amazing items, place bids in real-time, and win exciting auctions. 
            Join our community of buyers and sellers today.
          </p>
          <ClientOnly fallback={
            <div className="space-x-4">
              <Link href="/auctions">
                <Button variant="outline" size="lg">Browse Auctions</Button>
              </Link>
            </div>
          }>
            {!user && (
              <div className="space-x-4">
                <Link href="/register">
                  <Button size="lg">Get Started</Button>
                </Link>
                <Link href="/auctions">
                  <Button variant="outline" size="lg">Browse Auctions</Button>
                </Link>
              </div>
            )}
            {user && (
              <div className="space-x-4">
                <Link href="/create-auction">
                  <Button size="lg">Create Auction</Button>
                </Link>
                <Link href="/auctions">
                  <Button variant="outline" size="lg">Browse Auctions</Button>
                </Link>
              </div>
            )}
          </ClientOnly>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card>
            <CardHeader>
              <CardTitle>Real-time Bidding</CardTitle>
              <CardDescription>
                Place bids instantly and see updates in real-time
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Secure Transactions</CardTitle>
              <CardDescription>
                Safe and secure bidding with JWT authentication
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Easy to Use</CardTitle>
              <CardDescription>
                Simple interface for both buyers and sellers
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Recent Auctions */}
        <div>
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Recent Auctions</h2>
            <Link href="/auctions">
              <Button variant="outline">View All</Button>
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Loading auctions...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-500 mb-4">{error}</p>
              <Button onClick={fetchRecentAuctions} variant="outline">
                Retry
              </Button>
            </div>
          ) : recentAuctions.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recentAuctions.map((auction) => (
                <Card key={auction.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg">{auction.title}</CardTitle>
                      <Badge className={getStatusColor(auction.status)}>
                        {auction.status}
                      </Badge>
                    </div>
                    <CardDescription className="line-clamp-2">
                      {auction.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        Starting Price: <span className="font-semibold">${auction.starting_price}</span>
                      </p>
                      <p className="text-sm text-gray-600">
                        Current Price: <span className="font-semibold text-green-600">${auction.current_price}</span>
                      </p>
                      <p className="text-sm text-gray-600">
                        Ends: {new Date(auction.ends_at).toLocaleDateString('en-US')}
                      </p>
                    </div>
                    <Link href={`/auctions/${auction.id}`} className="block mt-4">
                      <Button className="w-full">View Details</Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No auctions available yet.</p>
              <ClientOnly>
                {user && (
                  <Link href="/create-auction">
                    <Button>Create the First Auction</Button>
                  </Link>
                )}
              </ClientOnly>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
