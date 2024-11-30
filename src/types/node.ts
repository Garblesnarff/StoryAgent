import { Node as ReactFlowNode, XYPosition } from 'reactflow';

/**
 * Data structure for story paragraph nodes
 */
export interface ParagraphData {
  /** Paragraph index in the story */
  index: number;
  /** Paragraph text content */
  text: string;
  /** Generated image URL if available */
  imageUrl?: string;
  /** Prompt used to generate the image */
  imagePrompt?: string;
  /** Generated audio URL if available */
  audioUrl?: string;
  /** Visual style applied to the node */
  style?: string;
  /** Error message if any operation failed */
  error?: string | null;
  /** Callback to generate all media for the paragraph */
  onGenerateCard?: () => Promise<void>;
  /** Callback to regenerate just the image */
  onRegenerateImage?: () => Promise<void>;
  /** Callback to regenerate just the audio */
  onRegenerateAudio?: () => Promise<void>;
  /** Callback when style is changed */
  onStyleChange?: (style: string) => void;
  /** Callback when text content is edited */
  onTextChange?: (text: string) => void;
}

/**
 * Type definition for story nodes in the flow editor
 */
export type StoryNode = ReactFlowNode<ParagraphData>;

/**
 * Node position type alias for clarity
 */
export type NodePosition = XYPosition;

/**
 * Edge data structure for node connections
 */
export interface EdgeData {
  /** Source node ID */
  sourceId: string;
  /** Target node ID */
  targetId: string;
  /** Optional label for the connection */
  label?: string;
}
