import { trellisClient } from '../utils/apiClient';
import { sleep } from '../utils/sceneHelpers';

export const useTrellis = () => {
  const generateCharacter = async (prompt: string) => {
    const submit = await trellisClient.post('/v1/generate', {
      type: 'text_to_3d',
      prompt,
      output_format: 'glb',
    });

    const taskId = submit.data?.id || submit.data?.task_id;
    if (!taskId) throw new Error('Trellis did not return a task id.');

    for (let i = 0; i < 60; i += 1) {
      await sleep(3000);
      const poll = await trellisClient.get(`/v1/generate/${taskId}`);
      const status = poll.data?.status;
      if (status === 'completed' || status === 'succeeded') {
        const glbUrl = poll.data?.result?.glb_url || poll.data?.output?.glb;
        if (!glbUrl) throw new Error('Trellis task completed but no GLB URL was returned.');
        return glbUrl as string;
      }
      if (status === 'failed') {
        throw new Error(poll.data?.error || 'Trellis generation failed.');
      }
    }

    throw new Error('Trellis generation timed out.');
  };

  return { generateCharacter };
};
