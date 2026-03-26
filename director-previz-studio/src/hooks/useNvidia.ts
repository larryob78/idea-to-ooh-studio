import { nvidiaClient } from '../utils/apiClient';

export const useNvidia = () => {
  const refinePrompt = async (input: string, mode: 'character' | 'world' = 'character') => {
    if (!input.trim()) return input;
    const system =
      mode === 'character'
        ? 'Refine this director prompt into vivid cinematic character blocking + costume + mood in under 80 words.'
        : 'Refine this world prompt into cinematic production design, atmosphere, scale, and lens-friendly details in under 90 words.';

    const response = await nvidiaClient.post('/v1/chat/completions', {
      model: 'meta/llama-3.1-70b-instruct',
      temperature: 0.5,
      max_tokens: 220,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: input },
      ],
    });

    return response.data?.choices?.[0]?.message?.content?.trim() || input;
  };

  return { refinePrompt };
};
