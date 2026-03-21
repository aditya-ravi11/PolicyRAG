import type { CompareQueryResponse } from '../types';

export const COMPARISON_EXAMPLES: CompareQueryResponse[] = [
  {
    query: 'What were Apple\'s total revenues in fiscal year 2023 and how did they compare to the prior year?',
    vanilla: {
      answer:
        'Apple\'s total revenues in fiscal year 2023 were approximately $383 billion, representing a slight decrease of about 3% compared to fiscal year 2022 revenues of $394 billion. The decline was primarily driven by lower iPhone and Mac sales, partially offset by growth in the Services segment which reached an all-time high of $85 billion.',
      latency_ms: 1240,
      provider: 'groq',
      model: 'llama-3.3-70b-versatile',
    },
    policyrag: {
      query_id: 'demo-1',
      query: 'What were Apple\'s total revenues in fiscal year 2023 and how did they compare to the prior year?',
      answer:
        'According to the filing, Apple\'s total net revenues for fiscal year 2023 were $383.3 billion [1], a decrease of approximately 2.8% from $394.3 billion in fiscal year 2022 [2]. The Services segment grew to $85.2 billion [3], reaching a record high. The Products segment declined to $298.1 billion from $316.2 billion in the prior year [2], driven primarily by lower iPhone and Mac sales due to macroeconomic headwinds [4].',
      citations: [
        {
          index: 1,
          chunk: {
            chunk_id: 'demo-c1',
            text: 'Total net revenues were $383,285 million for the fiscal year ended September 30, 2023.',
            section: 'Consolidated Statements of Operations',
            relevance_score: 0.95,
            company: 'Apple Inc.',
            filing_type: '10-K',
          },
          is_faithful: true,
        },
        {
          index: 2,
          chunk: {
            chunk_id: 'demo-c2',
            text: 'Total net revenues decreased 3% or $11.0 billion during 2023 compared to 2022, driven primarily by lower Products net revenues, partially offset by higher Services net revenues.',
            section: "Management's Discussion and Analysis",
            relevance_score: 0.92,
            company: 'Apple Inc.',
            filing_type: '10-K',
          },
          is_faithful: true,
        },
        {
          index: 3,
          chunk: {
            chunk_id: 'demo-c3',
            text: 'Services net revenues were $85,200 million in 2023, an increase from $78,129 million in 2022.',
            section: 'Revenue Breakdown',
            relevance_score: 0.88,
            company: 'Apple Inc.',
            filing_type: '10-K',
          },
          is_faithful: true,
        },
        {
          index: 4,
          chunk: {
            chunk_id: 'demo-c4',
            text: 'The Company experienced headwinds from foreign exchange and macroeconomic uncertainty affecting consumer demand.',
            section: 'Risk Factors',
            relevance_score: 0.72,
            company: 'Apple Inc.',
            filing_type: '10-K',
          },
          is_faithful: true,
        },
      ],
      source_chunks: [],
      evaluation: {
        faithfulness: 0.95,
        hallucination_score: 0.05,
        citation_precision: 1.0,
        citation_recall: 0.88,
        context_relevance: 0.91,
        completeness: 0.85,
        overall_trust_score: 0.92,
      },
      metadata: {
        provider: 'groq',
        model: 'llama-3.3-70b-versatile',
        num_chunks_retrieved: 10,
        latency_retrieval_ms: 45,
        latency_generation_ms: 1380,
        latency_evaluation_ms: 2100,
      },
    },
  },
  {
    query: 'Did Tesla report any cybersecurity incidents in their most recent filing?',
    vanilla: {
      answer:
        'Yes, Tesla reported several cybersecurity incidents including a data breach in Q3 2023 that affected approximately 75,000 employees. The breach exposed personal information including social security numbers and was attributed to insider misuse.',
      latency_ms: 980,
      provider: 'groq',
      model: 'llama-3.3-70b-versatile',
    },
    policyrag: {
      query_id: 'demo-2',
      query: 'Did Tesla report any cybersecurity incidents in their most recent filing?',
      answer:
        'Based on the provided context, there is no specific mention of cybersecurity incidents in the retrieved sections of Tesla\'s filing [1]. The filing discusses cybersecurity risk factors and the company\'s security program [2], but does not disclose any specific incidents in the portions available. I cannot confirm or deny whether incidents occurred outside the provided context.',
      citations: [
        {
          index: 1,
          chunk: {
            chunk_id: 'demo-c5',
            text: 'We are subject to cybersecurity risks including unauthorized access, data breaches, and other security incidents that could harm our business.',
            section: 'Risk Factors',
            relevance_score: 0.78,
            company: 'Tesla Inc.',
            filing_type: '10-K',
          },
          is_faithful: true,
        },
        {
          index: 2,
          chunk: {
            chunk_id: 'demo-c6',
            text: 'We maintain a comprehensive cybersecurity program overseen by our Chief Information Security Officer, including regular assessments and incident response planning.',
            section: 'Cybersecurity',
            relevance_score: 0.74,
            company: 'Tesla Inc.',
            filing_type: '10-K',
          },
          is_faithful: true,
        },
      ],
      source_chunks: [],
      evaluation: {
        faithfulness: 1.0,
        hallucination_score: 0.0,
        citation_precision: 1.0,
        citation_recall: 1.0,
        context_relevance: 0.76,
        completeness: 0.6,
        overall_trust_score: 0.88,
      },
      metadata: {
        provider: 'groq',
        model: 'llama-3.3-70b-versatile',
        num_chunks_retrieved: 10,
        latency_retrieval_ms: 38,
        latency_generation_ms: 1150,
        latency_evaluation_ms: 1800,
      },
    },
  },
];
