'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export default function CreateAuctionPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    starting_price: '',
    ends_at: ''
  });

  // Redirect if not logged in
  if (!user) {
    router.push('/login');
    return null;
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.title.trim()) {
      toast.error('Title is required');
      return;
    }
    
    if (!formData.description.trim()) {
      toast.error('Description is required');
      return;
    }
    
    const startingPrice = parseFloat(formData.starting_price);
    if (isNaN(startingPrice) || startingPrice <= 0) {
      toast.error('Starting price must be a positive number');
      return;
    }
    
    const endDate = new Date(formData.ends_at);
    const now = new Date();
    if (endDate <= now) {
      toast.error('End date must be in the future');
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiClient.createAuction({
        title: formData.title.trim(),
        description: formData.description.trim(),
        starting_price: startingPrice,
        ends_at: endDate.toISOString()
      });

      if (response.success) {
        toast.success('Auction created successfully!');
        router.push('/auctions');
      } else {
        toast.error(response.message || 'Failed to create auction');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to create auction');
    } finally {
      setIsLoading(false);
    }
  };

  // Get minimum date-time (current time + 1 hour)
  const getMinDateTime = () => {
    const now = new Date();
    now.setHours(now.getHours() + 1);
    return now.toISOString().slice(0, 16);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="max-w-2xl mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>Create New Auction</CardTitle>
            <CardDescription>
              List your item for auction and let bidders compete for it
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <Label htmlFor="title">Auction Title</Label>
                <Input
                  id="title"
                  name="title"
                  type="text"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="Enter a descriptive title for your auction"
                  required
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  name="description"
                  type="text"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Describe your item in detail"
                  required
                />
              </div>

              <div>
                <Label htmlFor="starting_price">Starting Price ($)</Label>
                <Input
                  id="starting_price"
                  name="starting_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={formData.starting_price}
                  onChange={handleInputChange}
                  placeholder="0.00"
                  required
                />
              </div>

              <div>
                <Label htmlFor="ends_at">Auction End Date & Time</Label>
                <Input
                  id="ends_at"
                  name="ends_at"
                  type="datetime-local"
                  value={formData.ends_at}
                  onChange={handleInputChange}
                  min={getMinDateTime()}
                  required
                />
                <p className="text-sm text-gray-600 mt-1">
                  Auction must end at least 1 hour from now
                </p>
              </div>

              <div className="flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1"
                >
                  {isLoading ? 'Creating...' : 'Create Auction'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
} 