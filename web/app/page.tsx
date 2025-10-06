'use client'

import { useState, useEffect, useRef } from "react";
import { Search, Lightbulb, MessageCircle, Sparkles, ArrowRight, TrendingUp, Calendar, AlertCircle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api, AnalysisStatus, AnalysisResult } from "@/lib/api";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!ticker.trim()) return;

    // Cleanup previous WebSocket if exists
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }

    setLoading(true);
    setError(null);
    setStatus(null);
    setResult(null);

    try {
      // First validate the ticker
      await api.validateTicker(ticker);

      // Start analysis with WebSocket for real-time updates
      const cleanup = await api.analyzeStockWithWebSocket(
        ticker,
        (statusUpdate) => {
          setStatus(statusUpdate);
        },
        (analysisResult) => {
          setResult(analysisResult);
          setLoading(false);
          setStatus(null);
        },
        (errorMessage) => {
          setError(errorMessage);
          setLoading(false);
          setStatus(null);
        }
      );

      cleanupRef.current = cleanup;

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
      setStatus(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Logo/Brand */}
          <div className="space-y-4">
            <h1 className="text-6xl md:text-7xl font-bold text-gray-900 tracking-tight">
              Few<span className="text-orange-500">Know</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 italic font-light">
              "few understand what actually happened since last earnings."
            </p>
          </div>

          {/* Description */}
          <p className="text-lg text-gray-700 max-w-2xl mx-auto leading-relaxed">
            Discover the real story behind earnings reports by connecting official announcements, 
            actual events, and community insights to reveal patterns others miss.
          </p>

          {/* Ticker Input */}
          <form onSubmit={handleSubmit} className="max-w-md mx-auto">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <Input
                  type="text"
                  placeholder="Enter ticker symbol (e.g., NVDA)"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  disabled={loading}
                  className="pl-10 h-12 bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-orange-500 focus:ring-orange-500 shadow-sm"
                />
              </div>
              <Button 
                type="submit" 
                size="lg" 
                disabled={loading || !ticker.trim()}
                className="bg-orange-500 hover:bg-orange-600 text-white px-6 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Analyzing...' : 'Analyze'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </form>

          {/* Status Display */}
          {status && (
            <Card className="max-w-md mx-auto bg-orange-50 border-orange-200">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      {status.message}
                    </span>
                    <span className="text-sm font-semibold text-orange-600">
                      {status.progress}
                    </span>
                  </div>
                  <div className="w-full bg-orange-200 rounded-full h-2">
                    <div 
                      className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: status.progress }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {error && (
            <Card className="max-w-md mx-auto bg-red-50 border-red-200">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900">Error</p>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results Display */}
          {result && result.insight_report && (
            <div className="mt-12 space-y-6 text-left">
              {/* Company Header */}
              {result.company_info && (
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-2xl text-gray-900">
                          {result.company_info.name}
                        </CardTitle>
                        <CardDescription className="text-gray-600 mt-1">
                          {result.company_info.ticker} • {result.company_info.sector} • {result.company_info.industry}
                        </CardDescription>
                      </div>
                      <CheckCircle2 className="h-8 w-8 text-green-500" />
                    </div>
                  </CardHeader>
                </Card>
              )}

              {/* Headline */}
              <Card className="bg-gradient-to-r from-orange-500 to-amber-500 border-0">
                <CardHeader>
                  <CardTitle className="text-2xl text-white">
                    {result.insight_report.headline}
                  </CardTitle>
                </CardHeader>
              </Card>

              {/* Price Performance */}
              {result.price_performance && (
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-orange-500" />
                      <CardTitle className="text-gray-900">Price Performance</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Since Earnings</p>
                        <p className="text-xl font-bold text-gray-900">{result.price_performance.since_earnings}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">vs S&P 500</p>
                        <p className="text-xl font-bold text-gray-900">{result.price_performance.vs_sp500}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">vs Sector</p>
                        <p className="text-xl font-bold text-gray-900">{result.price_performance.vs_sector}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Current Price</p>
                        <p className="text-xl font-bold text-gray-900">{result.price_performance.current_price}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* The Story */}
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">📖 The Story</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-line leading-relaxed">
                    {result.insight_report.story}
                  </p>
                </CardContent>
              </Card>

              {/* Retail Perspective */}
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">💬 Retail Perspective</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-line leading-relaxed">
                    {result.insight_report.retail_perspective}
                  </p>
                </CardContent>
              </Card>

              {/* The Gap */}
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">🔍 The Gap</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-line leading-relaxed">
                    {result.insight_report.the_gap}
                  </p>
                </CardContent>
              </Card>

              {/* What's Next */}
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">🔮 What's Next</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-line leading-relaxed">
                    {result.insight_report.whats_next}
                  </p>
                </CardContent>
              </Card>

              {/* Timeline */}
              {result.insight_report.key_dates && result.insight_report.key_dates.length > 0 && (
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-orange-500" />
                      <CardTitle className="text-gray-900">Key Timeline</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {result.insight_report.key_dates.map((event, idx) => (
                        <div key={idx} className="flex gap-4">
                          <div className="flex-shrink-0 w-24 text-sm text-gray-600">
                            {event.date}
                          </div>
                          <div className="flex-1">
                            <p className="text-gray-900">{event.description}</p>
                            <p className="text-xs text-gray-500 mt-1">{event.source}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Sources */}
              {result.insight_report.sources && result.insight_report.sources.length > 0 && (
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <CardTitle className="text-sm text-gray-900">Sources</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-1">
                      {result.insight_report.sources.map((source, idx) => (
                        <li key={idx} className="text-xs text-gray-600">• {source}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Feature Cards (only show when no results) */}
          {!result && (
            <div className="grid md:grid-cols-3 gap-6 mt-16 text-left">
              <Card className="bg-white border-gray-200 hover:border-orange-300 hover:shadow-lg transition-all">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center mb-4">
                    <Lightbulb className="h-6 w-6 text-orange-500" />
                  </div>
                  <CardTitle className="text-gray-900">Real Insights</CardTitle>
                  <CardDescription className="text-gray-600">
                    Connect expectations vs reality to understand what actually drove performance changes
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="bg-white border-gray-200 hover:border-orange-300 hover:shadow-lg transition-all">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-amber-100 flex items-center justify-center mb-4">
                    <MessageCircle className="h-6 w-6 text-amber-600" />
                  </div>
                  <CardTitle className="text-gray-900">Community Voice</CardTitle>
                  <CardDescription className="text-gray-600">
                    Discover what community discussions reveal before it becomes mainstream knowledge
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="bg-white border-gray-200 hover:border-orange-300 hover:shadow-lg transition-all">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center mb-4">
                    <Sparkles className="h-6 w-6 text-orange-500" />
                  </div>
                  <CardTitle className="text-gray-900">AI-Powered Analysis</CardTitle>
                  <CardDescription className="text-gray-600">
                    Surface non-obvious patterns and connections across multiple data sources
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          )}

          {/* Footer */}
          <div className="mt-16 pt-8 border-t border-gray-200">
            <p className="text-gray-500 text-sm">
              Powered by Claude AI • Data from public sources
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
