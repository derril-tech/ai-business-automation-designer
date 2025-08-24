/**
 * End-to-End Tests for AI Business Automation Designer Flow Builder
 * Tests complete user journeys from design to execution
 */

import { test, expect, Page } from '@playwright/test';

// Test data
const TEST_WORKFLOW = {
  name: 'Test Email Processing Workflow',
  description: 'Process incoming emails and send notifications',
  goal: 'Create a workflow to process incoming emails and send Slack notifications for high priority emails'
};

const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123'
};

test.describe('Flow Builder End-to-End Tests', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    // Navigate to the application
    await page.goto('http://localhost:3001');
    
    // Wait for the app to load
    await page.waitForSelector('[data-testid="flow-builder"]', { timeout: 10000 });
  });

  test.describe('Complete Workflow Design Journey', () => {
    test('should create a complete workflow using AI design', async () => {
      // 1. Start with AI Design
      await test.step('AI Design Interface', async () => {
        // Open AI design panel
        await page.click('[data-testid="ai-design-button"]');
        await expect(page.locator('[data-testid="ai-design-panel"]')).toBeVisible();

        // Enter workflow goal
        await page.fill('[data-testid="goal-input"]', TEST_WORKFLOW.goal);
        
        // Add constraints
        await page.fill('[data-testid="constraints-input"]', 'Use email and Slack connectors');
        
        // Submit AI design request
        await page.click('[data-testid="generate-workflow-button"]');
        
        // Wait for AI response
        await expect(page.locator('[data-testid="ai-loading"]')).toBeVisible();
        await expect(page.locator('[data-testid="workflow-preview"]')).toBeVisible({ timeout: 30000 });
      });

      // 2. Review and Edit Generated Workflow
      await test.step('Workflow Review and Editing', async () => {
        // Check that workflow was generated
        await expect(page.locator('[data-testid="workflow-name"]')).toContainText('Email');
        
        // Review generated steps
        const steps = page.locator('[data-testid="workflow-step"]');
        await expect(steps).toHaveCount(4); // Should have 4 steps
        
        // Edit workflow name
        await page.click('[data-testid="edit-workflow-name"]');
        await page.fill('[data-testid="workflow-name-input"]', TEST_WORKFLOW.name);
        await page.press('[data-testid="workflow-name-input"]', 'Enter');
        
        // Save workflow
        await page.click('[data-testid="save-workflow-button"]');
        await expect(page.locator('[data-testid="save-success"]')).toBeVisible();
      });

      // 3. Test Visual Flow Builder
      await test.step('Visual Flow Builder Interaction', async () => {
        // Switch to visual builder
        await page.click('[data-testid="visual-builder-tab"]');
        await expect(page.locator('[data-testid="flow-canvas"]')).toBeVisible();
        
        // Verify nodes are displayed
        const nodes = page.locator('[data-testid="flow-node"]');
        await expect(nodes).toHaveCount(4);
        
        // Test node selection
        await page.click('[data-testid="flow-node"]:first-child');
        await expect(page.locator('[data-testid="node-panel"]')).toBeVisible();
        
        // Test node configuration
        await page.click('[data-testid="configure-node-button"]');
        await expect(page.locator('[data-testid="node-config-modal"]')).toBeVisible();
        
        // Close configuration
        await page.click('[data-testid="close-modal-button"]');
      });

      // 4. Test Workflow Validation
      await test.step('Workflow Validation', async () => {
        // Run validation
        await page.click('[data-testid="validate-workflow-button"]');
        await expect(page.locator('[data-testid="validation-results"]')).toBeVisible();
        
        // Check validation status
        const validationStatus = page.locator('[data-testid="validation-status"]');
        await expect(validationStatus).toContainText('Valid');
      });

      // 5. Test Workflow Simulation
      await test.step('Workflow Simulation', async () => {
        // Open simulation panel
        await page.click('[data-testid="simulation-panel-button"]');
        await expect(page.locator('[data-testid="simulation-panel"]')).toBeVisible();
        
        // Configure simulation
        await page.fill('[data-testid="initial-variables-input"]', JSON.stringify({
          test_email: {
            subject: 'Test High Priority Email',
            priority: 'high',
            body: 'This is a test email'
          }
        }));
        
        // Start simulation
        await page.click('[data-testid="start-simulation-button"]');
        await expect(page.locator('[data-testid="simulation-running"]')).toBeVisible();
        
        // Wait for simulation completion
        await expect(page.locator('[data-testid="simulation-completed"]')).toBeVisible({ timeout: 30000 });
        
        // Check simulation results
        await expect(page.locator('[data-testid="simulation-results"]')).toBeVisible();
        const results = page.locator('[data-testid="step-result"]');
        await expect(results).toHaveCount(4);
      });

      // 6. Test Workflow Execution
      await test.step('Workflow Execution', async () => {
        // Open execution panel
        await page.click('[data-testid="execution-panel-button"]');
        await expect(page.locator('[data-testid="execution-panel"]')).toBeVisible();
        
        // Configure execution
        await page.fill('[data-testid="execution-variables-input"]', JSON.stringify({
          test_mode: true
        }));
        
        // Start execution
        await page.click('[data-testid="start-execution-button"]');
        await expect(page.locator('[data-testid="execution-running"]')).toBeVisible();
        
        // Wait for execution completion
        await expect(page.locator('[data-testid="execution-completed"]')).toBeVisible({ timeout: 30000 });
        
        // Check execution results
        await expect(page.locator('[data-testid="execution-results"]')).toBeVisible();
      });
    });

    test('should handle manual workflow creation', async () => {
      // 1. Start with empty canvas
      await test.step('Empty Canvas Setup', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        await expect(page.locator('[data-testid="flow-canvas"]')).toBeVisible();
        await expect(page.locator('[data-testid="node-palette"]')).toBeVisible();
      });

      // 2. Add nodes manually
      await test.step('Manual Node Addition', async () => {
        // Add HTTP connector node
        await page.dragAndDrop(
          '[data-testid="node-type-connector"]',
          '[data-testid="flow-canvas"]'
        );
        await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(1);
        
        // Configure HTTP node
        await page.click('[data-testid="flow-node"]:first-child');
        await page.click('[data-testid="configure-node-button"]');
        await page.selectOption('[data-testid="connector-type-select"]', 'http');
        await page.fill('[data-testid="http-url-input"]', 'https://httpbin.org/get');
        await page.selectOption('[data-testid="http-method-select"]', 'GET');
        await page.click('[data-testid="save-node-config"]');
        
        // Add transform node
        await page.dragAndDrop(
          '[data-testid="node-type-transform"]',
          '[data-testid="flow-canvas"]'
        );
        await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(2);
        
        // Connect nodes
        await page.dragAndDrop(
          '[data-testid="node-handle-source"]:first-child',
          '[data-testid="node-handle-target"]:last-child'
        );
        await expect(page.locator('[data-testid="flow-edge"]')).toHaveCount(1);
      });

      // 3. Save workflow
      await test.step('Workflow Saving', async () => {
        await page.click('[data-testid="save-workflow-button"]');
        await page.fill('[data-testid="workflow-name-input"]', 'Manual Test Workflow');
        await page.fill('[data-testid="workflow-description-input"]', 'Manually created test workflow');
        await page.click('[data-testid="confirm-save-button"]');
        await expect(page.locator('[data-testid="save-success"]')).toBeVisible();
      });
    });

    test('should handle workflow errors gracefully', async () => {
      // 1. Create workflow with errors
      await test.step('Error Workflow Creation', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        
        // Add invalid HTTP node
        await page.dragAndDrop(
          '[data-testid="node-type-connector"]',
          '[data-testid="flow-canvas"]'
        );
        await page.click('[data-testid="flow-node"]:first-child');
        await page.click('[data-testid="configure-node-button"]');
        await page.fill('[data-testid="http-url-input"]', 'invalid-url');
        await page.click('[data-testid="save-node-config"]');
      });

      // 2. Test validation errors
      await test.step('Validation Error Handling', async () => {
        await page.click('[data-testid="validate-workflow-button"]');
        await expect(page.locator('[data-testid="validation-errors"]')).toBeVisible();
        
        const errorMessage = page.locator('[data-testid="error-message"]');
        await expect(errorMessage).toContainText('Invalid URL');
      });

      // 3. Test execution errors
      await test.step('Execution Error Handling', async () => {
        await page.click('[data-testid="execution-panel-button"]');
        await page.click('[data-testid="start-execution-button"]');
        
        // Should show error handling options
        await expect(page.locator('[data-testid="error-handling-options"]')).toBeVisible();
        
        // Configure error handling
        await page.check('[data-testid="continue-on-error-checkbox"]');
        await page.click('[data-testid="retry-execution-button"]');
        
        // Should complete with errors
        await expect(page.locator('[data-testid="execution-completed-with-errors"]')).toBeVisible({ timeout: 30000 });
      });
    });
  });

  test.describe('User Interface and Experience', () => {
    test('should provide responsive design', async () => {
      // Test mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Check mobile layout
      await expect(page.locator('[data-testid="mobile-sidebar-toggle"]')).toBeVisible();
      await page.click('[data-testid="mobile-sidebar-toggle"]');
      await expect(page.locator('[data-testid="sidebar-panel"]')).toBeVisible();
      
      // Test tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();
      
      // Test desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
      await expect(page.locator('[data-testid="desktop-layout"]')).toBeVisible();
    });

    test('should support keyboard navigation', async () => {
      // Test keyboard shortcuts
      await page.keyboard.press('Control+n'); // New workflow
      await expect(page.locator('[data-testid="new-workflow-modal"]')).toBeVisible();
      
      await page.keyboard.press('Escape'); // Close modal
      await expect(page.locator('[data-testid="new-workflow-modal"]')).not.toBeVisible();
      
      await page.keyboard.press('Control+s'); // Save workflow
      await expect(page.locator('[data-testid="save-workflow-modal"]')).toBeVisible();
      
      await page.keyboard.press('Control+z'); // Undo
      await expect(page.locator('[data-testid="undo-notification"]')).toBeVisible();
    });

    test('should provide accessibility features', async () => {
      // Test screen reader support
      await expect(page.locator('[data-testid="flow-canvas"]')).toHaveAttribute('aria-label');
      await expect(page.locator('[data-testid="flow-node"]')).toHaveAttribute('role', 'button');
      
      // Test focus management
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="ai-design-button"]')).toBeFocused();
      
      // Test color contrast
      const canvas = page.locator('[data-testid="flow-canvas"]');
      const computedStyle = await canvas.evaluate((el) => {
        const style = window.getComputedStyle(el);
        return {
          backgroundColor: style.backgroundColor,
          color: style.color
        };
      });
      
      // Verify sufficient contrast (simplified check)
      expect(computedStyle.backgroundColor).not.toBe('transparent');
      expect(computedStyle.color).not.toBe('transparent');
    });
  });

  test.describe('Performance and Load Testing', () => {
    test('should handle large workflows', async () => {
      // Create workflow with many nodes
      await test.step('Large Workflow Creation', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        
        // Add 20 nodes
        for (let i = 0; i < 20; i++) {
          await page.dragAndDrop(
            '[data-testid="node-type-transform"]',
            '[data-testid="flow-canvas"]'
          );
          await page.waitForTimeout(100); // Small delay to prevent overwhelming
        }
        
        await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(20);
      });

      // Test canvas performance
      await test.step('Canvas Performance', async () => {
        // Measure render time
        const startTime = Date.now();
        await page.waitForSelector('[data-testid="flow-node"]:nth-child(20)');
        const renderTime = Date.now() - startTime;
        
        // Should render within reasonable time
        expect(renderTime).toBeLessThan(5000);
      });

      // Test zoom and pan performance
      await test.step('Zoom and Pan Performance', async () => {
        // Test zoom in
        await page.mouse.wheel(0, -100);
        await expect(page.locator('[data-testid="zoom-level"]')).toContainText('110%');
        
        // Test pan
        await page.mouse.down();
        await page.mouse.move(100, 100);
        await page.mouse.up();
        
        // Should remain responsive
        await expect(page.locator('[data-testid="flow-canvas"]')).toBeVisible();
      });
    });

    test('should handle concurrent operations', async () => {
      // Test multiple simultaneous operations
      await test.step('Concurrent Operations', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        
        // Start multiple operations simultaneously
        const operations = [
          page.click('[data-testid="ai-design-button"]'),
          page.click('[data-testid="simulation-panel-button"]'),
          page.click('[data-testid="execution-panel-button"]')
        ];
        
        await Promise.all(operations);
        
        // All panels should be visible
        await expect(page.locator('[data-testid="ai-design-panel"]')).toBeVisible();
        await expect(page.locator('[data-testid="simulation-panel"]')).toBeVisible();
        await expect(page.locator('[data-testid="execution-panel"]')).toBeVisible();
      });
    });
  });

  test.describe('Data Persistence and State Management', () => {
    test('should persist workflow state', async () => {
      // Create workflow
      await test.step('Workflow Creation and Persistence', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        await page.fill('[data-testid="workflow-name-input"]', 'Persistent Test Workflow');
        await page.click('[data-testid="save-workflow-button"]');
        await expect(page.locator('[data-testid="save-success"]')).toBeVisible();
      });

      // Refresh page and check persistence
      await test.step('State Persistence After Refresh', async () => {
        await page.reload();
        await page.waitForSelector('[data-testid="flow-builder"]');
        
        // Should show saved workflow
        await expect(page.locator('[data-testid="workflow-name"]')).toContainText('Persistent Test Workflow');
      });
    });

    test('should handle undo/redo operations', async () => {
      // Create workflow with multiple operations
      await test.step('Undo/Redo Operations', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        
        // Add node
        await page.dragAndDrop(
          '[data-testid="node-type-connector"]',
          '[data-testid="flow-canvas"]'
        );
        await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(1);
        
        // Undo
        await page.click('[data-testid="undo-button"]');
        await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(0);
        
        // Redo
        await page.click('[data-testid="redo-button"]');
        await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(1);
      });
    });
  });

  test.describe('Error Recovery and Resilience', () => {
    test('should recover from network errors', async () => {
      // Simulate network error during AI design
      await test.step('Network Error Recovery', async () => {
        await page.route('**/api/v1/design/ai-design', route => {
          route.abort('failed');
        });
        
        await page.click('[data-testid="ai-design-button"]');
        await page.fill('[data-testid="goal-input"]', TEST_WORKFLOW.goal);
        await page.click('[data-testid="generate-workflow-button"]');
        
        // Should show error message
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
        
        // Restore network and retry
        await page.unroute('**/api/v1/design/ai-design');
        await page.click('[data-testid="retry-button"]');
        await expect(page.locator('[data-testid="workflow-preview"]')).toBeVisible({ timeout: 30000 });
      });
    });

    test('should handle browser crashes gracefully', async () => {
      // Test auto-save functionality
      await test.step('Auto-save and Recovery', async () => {
        await page.click('[data-testid="new-workflow-button"]');
        await page.fill('[data-testid="workflow-name-input"]', 'Auto-save Test Workflow');
        
        // Wait for auto-save
        await page.waitForTimeout(2000);
        await expect(page.locator('[data-testid="auto-save-indicator"]')).toBeVisible();
        
        // Simulate page reload (like after crash)
        await page.reload();
        await page.waitForSelector('[data-testid="flow-builder"]');
        
        // Should show recovery dialog
        await expect(page.locator('[data-testid="recovery-dialog"]')).toBeVisible();
        await page.click('[data-testid="restore-workflow-button"]');
        
        // Should restore workflow
        await expect(page.locator('[data-testid="workflow-name"]')).toContainText('Auto-save Test Workflow');
      });
    });
  });
});

// Helper functions for common operations
async function createTestWorkflow(page: Page) {
  await page.click('[data-testid="new-workflow-button"]');
  await page.fill('[data-testid="workflow-name-input"]', TEST_WORKFLOW.name);
  await page.fill('[data-testid="workflow-description-input"]', TEST_WORKFLOW.description);
  await page.click('[data-testid="save-workflow-button"]');
  await expect(page.locator('[data-testid="save-success"]')).toBeVisible();
}

async function addNodeToCanvas(page: Page, nodeType: string) {
  await page.dragAndDrop(
    `[data-testid="node-type-${nodeType}"]`,
    '[data-testid="flow-canvas"]'
  );
  await expect(page.locator('[data-testid="flow-node"]')).toHaveCount(1);
}

async function configureNode(page: Page, config: Record<string, any>) {
  await page.click('[data-testid="flow-node"]:first-child');
  await page.click('[data-testid="configure-node-button"]');
  
  for (const [key, value] of Object.entries(config)) {
    await page.fill(`[data-testid="${key}-input"]`, value);
  }
  
  await page.click('[data-testid="save-node-config"]');
}
