import React from 'react';

interface Props {
  originalUrl: string | null;
  maskCoarse?: string;
  maskLesion?: string;
  showCoarse: boolean;
  showLesion: boolean;
}

const ImageOverlay: React.FC<Props> = ({
  originalUrl,
  maskCoarse,
  maskLesion,
  showCoarse,
  showLesion,
}) => {
  return (
    <div className="relative w-48 h-48 bg-black rounded-lg overflow-hidden border border-gray-600 group">
      
      {originalUrl ? (
        <img
          src={originalUrl}
          alt="CT"
          className="absolute inset-0 w-full h-full object-contain z-0"
        />
      ) : (
        <div className="flex items-center justify-center h-full text-xs text-gray-500">
          No Image
        </div>
      )}

      
      {showCoarse && maskCoarse && (
        <img
          src={maskCoarse}
          alt="Lung"
          className="absolute inset-0 w-full h-full object-contain z-10 mix-blend-screen pointer-events-none filter sepia hue-rotate-180 saturate-200"
        />
      )}

      
      {showLesion && maskLesion && (
        <img
          src={maskLesion}
          alt="Lesion"
          className="absolute inset-0 w-full h-full object-contain z-20  mix-blend-screen pointer-events-none filter drop-shadow-md sepia saturate-[50] hue-rotate-[-50deg]"
        />
      )}

      
      <div className="absolute bottom-1 right-1 z-30 flex gap-1">
        {showCoarse && maskCoarse && (
          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm border border-white/50" title="Vùng Tổn thương tổng quan"></span>
        )}
        {showLesion && maskLesion && (
          <span className="w-2 h-2 rounded-full bg-red-500 shadow-sm border border-white/50" title="Vùng Tổn thương chi tiết"></span>
        )}
      </div>
    </div>
  );
};

export default ImageOverlay;