#!/usr/bin/env node

/**
 * AI Peer Review MCP Server
 * Provides peer review feedback using Google Gemini API
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs';
import path from 'path';

// Setup logging
const logFile = path.join(process.cwd(), 'mcp-server.log');

function log(message, data = null) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ${message}${data ? '\n' + JSON.stringify(data, null, 2) : ''}\n`;
  
  // Write to file
  fs.appendFileSync(logFile, logEntry);
  
  // Also write to stderr (won't interfere with MCP stdio communication)
  console.error(`[MCP LOG] ${message}`, data || '');
}

// Initialize the MCP server
const server = new Server(
  {
    name: 'ai-peer-review',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Google Gemini API configuration
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

/**
 * Call Google Gemini API for peer review
 */
async function getGeminiReview(userQuestion, initialAnswer) {
  if (!GEMINI_API_KEY) {
    throw new Error('GEMINI_API_KEY environment variable is required');
  }

  const reviewPrompt = `PEER REVIEW REQUEST:

Original Question: "${userQuestion}"

Initial AI Response: "${initialAnswer}"

Please provide constructive peer review feedback in the following format:

ACCURACY ASSESSMENT:
[Evaluate factual correctness and identify any errors]

COMPLETENESS:
[Identify important points or perspectives that are missing]

CLARITY:
[Suggest ways to improve explanation clarity and structure]

IMPROVEMENT SUGGESTIONS:
[Provide specific, actionable suggestions for enhancement]

OVERALL RATING:
[Provide a brief overall assessment: Excellent/Good/Needs Improvement/Poor]

Be constructive, specific, and helpful in your feedback.`;

  log('Sending request to Gemini', {
    question: userQuestion,
    answer: initialAnswer.substring(0, 200) + '...',
    promptLength: reviewPrompt.length
  });

  try {
    const response = await fetch(GEMINI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY,
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: reviewPrompt
          }]
        }]
      })
    });

    log('Gemini API response status', { status: response.status, statusText: response.statusText });

    if (!response.ok) {
      const errorText = await response.text();
      log('Gemini API error details', { status: response.status, error: errorText });
      throw new Error(`Gemini API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    log('Raw Gemini response', data);
    
    if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
      log('Invalid Gemini response structure', data);
      throw new Error('Invalid response from Gemini API');
    }

    const geminiReview = data.candidates[0].content.parts[0].text;
    log('Gemini review text', { review: geminiReview });

    return geminiReview;
  } catch (error) {
    log('Error in getGeminiReview', { error: error.message });
    throw new Error(`Failed to get Gemini review: ${error.message}`);
  }
}

/**
 * Parse structured feedback from Gemini response
 */
function parseGeminiFeedback(rawFeedback) {
  const sections = {
    accuracy_assessment: '',
    completeness: '',
    clarity: '',
    improvement_suggestions: '',
    overall_rating: ''
  };

  const patterns = {
    accuracy_assessment: /ACCURACY ASSESSMENT:\s*([\s\S]*?)(?=COMPLETENESS:|$)/i,
    completeness: /COMPLETENESS:\s*([\s\S]*?)(?=CLARITY:|$)/i,
    clarity: /CLARITY:\s*([\s\S]*?)(?=IMPROVEMENT SUGGESTIONS:|$)/i,
    improvement_suggestions: /IMPROVEMENT SUGGESTIONS:\s*([\s\S]*?)(?=OVERALL RATING:|$)/i,
    overall_rating: /OVERALL RATING:\s*([\s\S]*?)$/i
  };

  for (const [key, pattern] of Object.entries(patterns)) {
    const match = rawFeedback.match(pattern);
    if (match) {
      sections[key] = match[1].trim();
    }
  }

  return sections;
}

// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'ai_peer_review',
        description: 'Get peer review feedback from Google Gemini on your response to help improve accuracy and completeness',
        inputSchema: {
          type: 'object',
          properties: {
            user_question: {
              type: 'string',
              description: 'The original question asked by the user'
            },
            my_answer: {
              type: 'string',
              description: 'Your initial response that needs peer review'
            }
          },
          required: ['user_question', 'my_answer']
        }
      }
    ]
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  log('Tool call received', { name, args: { question: args.user_question?.substring(0, 100) + '...', answer: args.my_answer?.substring(0, 100) + '...' } });

  if (name === 'ai_peer_review') {
    try {
      const { user_question, my_answer } = args;
      
      if (!user_question || !my_answer) {
        throw new Error('Both user_question and my_answer are required');
      }

      log('Starting peer review process');

      // Get review from Gemini
      const rawFeedback = await getGeminiReview(user_question, my_answer);
      
      // Parse the structured feedback
      const structuredFeedback = parseGeminiFeedback(rawFeedback);
      log('Parsed feedback', structuredFeedback);
      
      const result = {
        peer_review_feedback: {
          ...structuredFeedback,
          raw_feedback: rawFeedback,
          reviewer: 'Google Gemini',
          timestamp: new Date().toISOString()
        },
        usage_note: "Use this feedback to identify areas for improvement in your response. Consider revising your answer to address the points raised in the peer review."
      };

      log('Sending result back to LMStudio', { resultSize: JSON.stringify(result).length });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }
        ]
      };
    } catch (error) {
      log('Error in ai_peer_review tool', { error: error.message });
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              error: error.message,
              suggestion: "The peer review service is currently unavailable. Please try again later or proceed with your original answer."
            }, null, 2)
          }
        ],
        isError: true
      };
    }
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Start the server
async function main() {
  log('Starting AI Peer Review MCP Server');
  const transport = new StdioServerTransport();
  await server.connect(transport);
  log('MCP Server connected and running on stdio');
  console.error('AI Peer Review MCP Server running on stdio');
}

main().catch((error) => {
  log('Server startup error', { error: error.message });
  console.error('Server error:', error);
  process.exit(1);
});
