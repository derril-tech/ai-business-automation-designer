import { CustomNode } from "./CustomNode"

export const nodeTypes = {
  connector: CustomNode,
  condition: CustomNode,
  transform: CustomNode,
  webhook: CustomNode,
  delay: CustomNode,
  start: CustomNode,
  end: CustomNode,
}

export const nodeCategories = {
  triggers: [
    { type: "start", label: "Start", icon: "play", color: "green" },
    { type: "webhook", label: "Webhook", icon: "webhook", color: "blue" },
  ],
  actions: [
    { type: "connector", label: "Connector", icon: "link", color: "purple" },
    { type: "transform", label: "Transform", icon: "settings", color: "orange" },
  ],
  logic: [
    { type: "condition", label: "Condition", icon: "git-branch", color: "yellow" },
    { type: "delay", label: "Delay", icon: "clock", color: "gray" },
  ],
  end: [
    { type: "end", label: "End", icon: "square", color: "red" },
  ],
}
