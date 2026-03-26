import { meshyClient } from '../utils/apiClient';
import { sleep } from '../utils/sceneHelpers';

export const useMeshy = () => {
  const generateCharacter = async (prompt: string) => {
    const submit = await meshyClient.post('/v2/text-to-3d', {
      mode: 'preview',
      prompt,
      art_style: 'realistic',
      should_remesh: true,
    });

    const taskId = submit.data?.id;
    if (!taskId) throw new Error('Meshy did not return a task id.');

    for (let i = 0; i < 60; i += 1) {
      await sleep(3000);
      const poll = await meshyClient.get(`/v2/text-to-3d/${taskId}`);
      const status = poll.data?.status;
      if (status === 'SUCCEEDED' || status === 'succeeded') {
        const glbUrl = poll.data?.model_urls?.glb || poll.data?.outputs?.glb;
        if (!glbUrl) throw new Error('Meshy task succeeded but no GLB URL was returned.');
        return glbUrl as string;
      }
      if (status === 'FAILED' || status === 'failed') {
        throw new Error(poll.data?.message || 'Meshy generation failed.');
      }
    }

    throw new Error('Meshy generation timed out.');
  };

  return { generateCharacter };
};
