export interface User {
  user_id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface SegmentResult {
  filename: string;
  mask_coarse: string;
  mask_lesion: string;
}

export interface SliceDetail {
  filename: string;
  label: string;
  confidence: string;
}

export interface PatientDiagnosis {
  final_label: string;
  final_confidence: string;
  mean_probs: { [key: string]: string };
}

export interface ClassificationResult {
  diagnosis: PatientDiagnosis | null;
  details: SliceDetail[];
}

export interface PreviewFile {
  name: string;
  url: string | null;
  file: File;
  isLoadingPreview: boolean;
  caption?: string;
  isGeneratingCaption?: boolean;
}