import { worldLabsClient } from '../utils/apiClient';
import { sleep } from '../utils/sceneHelpers';

export const useWorldLabs = () => {
  const generateWorld = async (prompt: string) => {
    const submit = await worldLabsClient.post('/v1/worlds/generate', {
      prompt,
      output: 'equirectangular',
      quality: 'high',
    });

    const taskId = submit.data?.id || submit.data?.task_id;
    if (!taskId) throw new Error('World Labs did not return a task id.');

    for (let i = 0; i < 60; i += 1) {
      await sleep(3000);
      const poll = await worldLabsClient.get(`/v1/worlds/generate/${taskId}`);
      const status = poll.data?.status;
      if (status === 'completed' || status === 'succeeded') {
        const textureUrl =
          poll.data?.result?.equirectangular_url || poll.data?.result?.hdr_url || poll.data?.output?.url;
        if (!textureUrl) throw new Error('World Labs completed without environment URL.');
        return textureUrl as string;
      }
      if (status === 'failed') {
        throw new Error(poll.data?.error || 'World generation failed.');
      }
    }

    throw new Error('World generation timed out.');
  };

  return { generateWorld };
};
