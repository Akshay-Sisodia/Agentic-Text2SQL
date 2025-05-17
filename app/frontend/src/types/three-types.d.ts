declare module '@react-three/fiber' {
  import { Camera, Object3D, Material, Group, WebGLRenderer } from 'three';
  import * as THREE from 'three';
  import * as React from 'react';

  export type ThreeEvent<T> = T & {
    object: Object3D;
    eventObject: Object3D;
    point: THREE.Vector3;
    normal: THREE.Vector3;
    intersections: Intersection[];
    stopped: boolean;
    distance: number;
    delta: number;
    unprojectedPoint: THREE.Vector3;
    ray: THREE.Ray;
    camera: Camera;
  };

  export interface Intersection extends THREE.Intersection {
    eventObject: Object3D;
  }

  export type ThreeComponents = Partial<{
    [K in keyof JSX.IntrinsicElements]: React.DetailedHTMLProps<
      React.HTMLAttributes<HTMLElement>,
      HTMLElement
    >;
  }>;

  export type ExtendedColors<T extends string> =
    | T
    | Exclude<
        | keyof typeof THREE
        | ConstructorParameters<typeof THREE.Color>[0],
        number | symbol
      >;

  export type MaterialProps = Partial<Material> & {
    [key: string]: any;
  };

  export type ThreeCanvasProps = React.PropsWithChildren<{
    children?: React.ReactNode;
    gl?: Partial<WebGLRenderer>;
    camera?: Partial<Camera>;
    scene?: Partial<THREE.Scene>;
    raycaster?: Partial<THREE.Raycaster>;
    shadowMap?: Partial<WebGLRenderer['shadowMap']>;
    pixelRatio?: number;
    flat?: boolean;
    orthographic?: boolean;
    frameloop?: 'always' | 'demand' | 'never';
    resize?: {
      scroll?: boolean;
      debounce?: { scroll?: number; resize?: number };
    };
    className?: string;
    dpr?: number | [number, number];
    style?: React.CSSProperties;
    onCreated?: (state: RootState) => void;
    onPointerMissed?: (event: MouseEvent) => void;
  }>;

  export type RootState = {
    gl: WebGLRenderer;
    scene: THREE.Scene;
    camera: Camera;
    raycaster: THREE.Raycaster;
    events: {
      handlers: any[];
      connected: any[];
      connect: (target: HTMLElement) => void;
      disconnect: () => void;
    };
    set: React.Dispatch<React.SetStateAction<Partial<RootState>>>;
    get: () => RootState;
    performance: {
      current: number;
      min: number;
      max: number;
      debounce: number;
      regress: () => void;
    };
    size: {
      width: number;
      height: number;
      top: number;
      left: number;
    };
    viewport: {
      width: number;
      height: number;
      factor: number;
    };
    setSize: (width: number, height: number) => void;
    setViewport: (element: HTMLElement) => void;
    setDpr: (dpr: number) => void;
    invalidate: () => void;
    advance: (timestamp: number, runGlobalEffects?: boolean) => void;
    legacy: boolean;
    linear: boolean;
    flat: boolean;
    controls: React.MutableRefObject<any>;
  };

  export function Canvas(props: ThreeCanvasProps): JSX.Element;
  export function useFrame(
    callback: (state: RootState, delta: number) => void,
    renderPriority?: number
  ): void;
  export function useThree(): RootState;
  export function extend(objects: object): void;
}

declare module '@react-three/drei' {
  import { Object3D, Material, Mesh, Group, BufferGeometry } from 'three';
  import { ReactNode } from 'react';

  export function OrbitControls(props: {
    makeDefault?: boolean;
    camera?: THREE.Camera;
    enableDamping?: boolean;
    enableZoom?: boolean;
    enablePan?: boolean;
    dampingFactor?: number;
    autoRotate?: boolean;
    autoRotateSpeed?: number;
    minPolarAngle?: number;
    maxPolarAngle?: number;
    minAzimuthAngle?: number;
    maxAzimuthAngle?: number;
    minDistance?: number;
    maxDistance?: number;
    zoomSpeed?: number;
    panSpeed?: number;
    rotateSpeed?: number;
    target?: [number, number, number];
    [key: string]: any;
  }): JSX.Element;

  export function PerspectiveCamera(props: {
    makeDefault?: boolean;
    position?: [number, number, number];
    fov?: number;
    zoom?: number;
    near?: number;
    far?: number;
    [key: string]: any;
  }): JSX.Element;

  export function Text(props: {
    children: ReactNode;
    color?: string;
    fontSize?: number;
    maxWidth?: number;
    lineHeight?: number;
    letterSpacing?: number;
    textAlign?: 'left' | 'right' | 'center' | 'justify';
    font?: string;
    anchorX?: number | 'left' | 'center' | 'right';
    anchorY?: number | 'top' | 'top-baseline' | 'middle' | 'bottom-baseline' | 'bottom';
    position?: [number, number, number];
    [key: string]: any;
  }): JSX.Element;

  export function Float(props: {
    speed?: number;
    rotationIntensity?: number;
    floatIntensity?: number;
    children: ReactNode;
    [key: string]: any;
  }): JSX.Element;
}

declare module '@react-three/postprocessing' {
  import { ReactNode } from 'react';

  export function EffectComposer(props: {
    enabled?: boolean;
    children: ReactNode;
    [key: string]: any;
  }): JSX.Element;

  export function Bloom(props: {
    intensity?: number;
    luminanceThreshold?: number;
    luminanceSmoothing?: number;
    [key: string]: any;
  }): JSX.Element;

  export function Vignette(props: {
    offset?: number;
    darkness?: number;
    eskil?: boolean;
    [key: string]: any;
  }): JSX.Element;
} 