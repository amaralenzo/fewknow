'use client'

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface ImageCarouselProps {
  images: string[];
  alt: string;
  maxHeight?: string;
}

export function ImageCarousel({ images, alt, maxHeight = "500px" }: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!images || images.length === 0) {
    return null;
  }

  const goToPrevious = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === 0 ? images.length - 1 : prevIndex - 1
    );
  };

  const goToNext = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === images.length - 1 ? 0 : prevIndex + 1
    );
  };

  const hasMultipleImages = images.length > 1;

  return (
    <div className="relative rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
      {/* Image */}
      <div className="relative" style={{ maxHeight }}>
        <img 
          src={images[currentIndex]} 
          alt={`${alt} - Image ${currentIndex + 1}`}
          className="w-full h-auto object-contain"
          style={{ maxHeight }}
          loading="lazy"
          onError={(e) => {
            // If image fails to load, try next one or hide
            if (hasMultipleImages && currentIndex < images.length - 1) {
              setCurrentIndex(currentIndex + 1);
            } else {
              e.currentTarget.style.display = 'none';
            }
          }}
        />
        
        {/* Navigation buttons - only show if multiple images */}
        {hasMultipleImages && (
          <>
            {/* Previous button */}
            <button
              onClick={goToPrevious}
              className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-all"
              aria-label="Previous image"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>

            {/* Next button */}
            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-all"
              aria-label="Next image"
            >
              <ChevronRight className="h-5 w-5" />
            </button>

            {/* Image counter */}
            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              {currentIndex + 1} / {images.length}
            </div>
          </>
        )}
      </div>

      {/* Dot indicators - only show if multiple images */}
      {hasMultipleImages && (
        <div className="flex justify-center gap-2 py-2 bg-gray-100">
          {images.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentIndex 
                  ? 'bg-orange-500 w-4' 
                  : 'bg-gray-400 hover:bg-gray-500'
              }`}
              aria-label={`Go to image ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
