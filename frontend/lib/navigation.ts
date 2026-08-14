import {
  ActivitySquare,
  AlertTriangle,
  Bot,
  Building2,
  Cuboid,
  ClipboardCheck,
  Monitor,
  Flame,
  Shield,
  Users,
  Waypoints,
} from "lucide-react";
import { type LucideIcon } from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export const navItems: NavItem[] = [
  { label: "Command Center", href: "/", icon: ActivitySquare },
  { label: "Twin Ecosystem", href: "/twins", icon: Building2 },
  { label: "Spatial Digital Twin", href: "/spatial", icon: Cuboid },
  { label: "Predictive Intelligence", href: "/prediction", icon: Bot },
  { label: "Explainable AI", href: "/explainability", icon: ClipboardCheck },
  { label: "Evacuation Optimizer", href: "/evacuation", icon: Waypoints },
  { label: "Scenario Lab", href: "/scenarios", icon: Flame },
  { label: "Emergency Response", href: "/response", icon: AlertTriangle },
  { label: "Governance & Security", href: "/governance", icon: Shield },
  { label: "ROI & Analytics", href: "/roi", icon: Users },
  { label: "Presentation Mode", href: "/presentation", icon: Monitor },
];
