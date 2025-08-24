"use client"

import { memo } from "react"
import { Handle, Position, NodeProps } from "reactflow"
import { cn } from "@/lib/utils"
import { 
  Play, 
  Webhook, 
  Link, 
  Settings, 
  GitBranch, 
  Clock, 
  Square,
  LucideIcon 
} from "lucide-react"

const iconMap: Record<string, LucideIcon> = {
  start: Play,
  webhook: Webhook,
  connector: Link,
  transform: Settings,
  condition: GitBranch,
  delay: Clock,
  end: Square,
}

const colorMap: Record<string, string> = {
  start: "bg-green-500",
  webhook: "bg-blue-500",
  connector: "bg-purple-500",
  transform: "bg-orange-500",
  condition: "bg-yellow-500",
  delay: "bg-gray-500",
  end: "bg-red-500",
}

export const CustomNode = memo(({ data, selected }: NodeProps) => {
  const Icon = iconMap[data.type] || Settings
  const colorClass = colorMap[data.type] || "bg-gray-500"

  return (
    <div
      className={cn(
        "rounded-lg border-2 bg-white p-3 shadow-sm transition-all",
        selected ? "border-blue-500 shadow-md" : "border-gray-200",
        "min-w-[150px]"
      )}
    >
      {/* Input Handle */}
      {data.type !== "start" && (
        <Handle
          type="target"
          position={Position.Top}
          className="w-3 h-3 bg-gray-400"
        />
      )}

      {/* Node Content */}
      <div className="flex items-center gap-2">
        <div className={cn("p-1 rounded", colorClass)}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{data.label}</div>
          {data.description && (
            <div className="text-xs text-gray-500 truncate">
              {data.description}
            </div>
          )}
        </div>
      </div>

      {/* Status indicator */}
      {data.status && (
        <div className="mt-2">
          <div className={cn(
            "text-xs px-2 py-1 rounded-full",
            data.status === "completed" && "bg-green-100 text-green-800",
            data.status === "running" && "bg-blue-100 text-blue-800",
            data.status === "failed" && "bg-red-100 text-red-800",
            data.status === "pending" && "bg-gray-100 text-gray-800"
          )}>
            {data.status}
          </div>
        </div>
      )}

      {/* Output Handle */}
      {data.type !== "end" && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 bg-gray-400"
        />
      )}
    </div>
  )
})

CustomNode.displayName = "CustomNode"
