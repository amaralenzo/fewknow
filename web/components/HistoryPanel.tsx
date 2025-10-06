'use client'

import { useState, useEffect } from "react";
import { AnalysisResult } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { History, X, Clock, TrendingUp } from "lucide-react";

interface HistoryEntry extends AnalysisResult {
  timestamp: string;
}

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAnalysis: (analysis: AnalysisResult) => void;
}

export function HistoryPanel({ isOpen, onClose, onSelectAnalysis }: HistoryPanelProps) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [mounted, setMounted] = useState(false);

  // Load history only on client-side after mount
  useEffect(() => {
    setMounted(true);
    const savedHistory = localStorage.getItem('analysisHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Reload history when panel opens (in case it was updated)
  useEffect(() => {
    if (isOpen && mounted) {
      const savedHistory = localStorage.getItem('analysisHistory');
      if (savedHistory) {
        setHistory(JSON.parse(savedHistory));
      }
    }
  }, [isOpen, mounted]);

  // Prevent rendering until mounted to avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const clearHistory = () => {
    if (confirm('Are you sure you want to clear all history?')) {
      localStorage.removeItem('analysisHistory');
      setHistory([]); // Update state immediately
      onClose();
    }
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div 
        className={`fixed top-0 right-0 h-full w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History className="h-5 w-5 text-orange-500" />
                <h2 className="text-xl font-bold text-gray-900">Analysis History</h2>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* History List */}
          <div className="flex-1 overflow-y-auto p-4">
            {history.length === 0 ? (
              <div className="text-center py-12">
                <History className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No analyses yet</p>
                <p className="text-sm text-gray-400 mt-1">Your past analyses will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((entry, idx) => (
                  <Card 
                    key={idx}
                    className="cursor-pointer hover:border-orange-300 hover:shadow-md transition-all"
                    onClick={() => {
                      onSelectAnalysis(entry);
                      onClose();
                    }}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg text-gray-900">
                            {entry.company_info?.ticker || entry.ticker}
                          </CardTitle>
                          <CardDescription className="text-sm">
                            {entry.company_info?.name}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-2">
                        {entry.price_performance && (
                          <div className="flex items-center gap-2 text-sm">
                            <TrendingUp className="h-4 w-4 text-orange-500" />
                            <span className="font-medium text-gray-900">
                              {entry.price_performance.since_earnings}
                            </span>
                            <span className="text-gray-500">since earnings</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          {formatDate(entry.timestamp)}
                        </div>
                        {entry.insight_report?.headline && (
                          <p className="text-xs text-gray-600 line-clamp-2 mt-2">
                            {entry.insight_report.headline}
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {history.length > 0 && (
            <div className="p-4 border-t border-gray-200">
              <Button
                variant="outline"
                size="sm"
                onClick={clearHistory}
                className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                Clear All History
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
