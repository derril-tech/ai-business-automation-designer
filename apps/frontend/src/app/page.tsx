"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  Sparkles, 
  Workflow, 
  Zap, 
  Globe, 
  Database, 
  Shield,
  ArrowRight,
  Play,
  Settings
} from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">AI Business Automation</h1>
            </div>
            <nav className="flex items-center gap-4">
              <Link href="/flow-builder">
                <Button>
                  <Workflow className="w-4 h-4 mr-2" />
                  Open Flow Builder
                </Button>
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge variant="secondary" className="mb-4">
            <Sparkles className="w-3 h-3 mr-1" />
            AI-Powered Workflow Design
          </Badge>
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Design & Execute Business Workflows with AI
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Create intelligent automation workflows using natural language. 
            Our AI-powered platform designs, validates, and executes complex business processes.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/flow-builder">
              <Button size="lg" className="text-lg px-8 py-4">
                <Play className="w-5 h-5 mr-2" />
                Start Building
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="text-lg px-8 py-4">
              <Settings className="w-5 h-5 mr-2" />
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Powerful Features for Modern Automation
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Everything you need to build, deploy, and manage intelligent business workflows
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-blue-600" />
                </div>
                <CardTitle>AI-Powered Design</CardTitle>
                <CardDescription>
                  Describe your workflow in natural language and let AI design the optimal automation flow
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <Workflow className="w-6 h-6 text-green-600" />
                </div>
                <CardTitle>Visual Flow Builder</CardTitle>
                <CardDescription>
                  Drag-and-drop interface for creating and editing workflows with real-time validation
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-purple-600" />
                </div>
                <CardTitle>Smart Execution</CardTitle>
                <CardDescription>
                  Intelligent execution engine with error handling, retries, and real-time monitoring
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                  <Globe className="w-6 h-6 text-orange-600" />
                </div>
                <CardTitle>100+ Integrations</CardTitle>
                <CardDescription>
                  Connect to popular services like Slack, Salesforce, databases, and custom APIs
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                  <Database className="w-6 h-6 text-red-600" />
                </div>
                <CardTitle>Data Transformation</CardTitle>
                <CardDescription>
                  Powerful data mapping and transformation tools for complex business logic
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-indigo-600" />
                </div>
                <CardTitle>Enterprise Security</CardTitle>
                <CardDescription>
                  Enterprise-grade security with role-based access control and audit trails
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Automate Your Business?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Start building intelligent workflows today and transform how your business operates
          </p>
          <Link href="/flow-builder">
            <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
              Get Started Now
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-blue-400" />
              <span className="text-lg font-semibold">AI Business Automation</span>
            </div>
            <div className="text-sm text-gray-400">
              © 2024 AI Business Automation Designer. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
