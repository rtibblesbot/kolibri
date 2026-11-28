import flushPromises from 'flush-promises';
import heartbeat from 'kolibri/heartbeat';
import router from 'kolibri/router';
import { UserKinds } from 'kolibri/constants';
import { clearError, error } from 'kolibri/utils/appError';
import { pageLoading } from 'kolibri-common/composables/usePageLoading';
import { showExam } from '../handlers';

describe('showExam', () => {
  let contentRequest;
  let sessionRequest;
  let holdSessionRequest;
  const session = { id: 'session', user_id: 'learner', kind: [UserKinds.LEARNER] };

  beforeEach(() => {
    holdSessionRequest = false;
    contentRequest = null;
    sessionRequest = null;
    router.initRouter();
    jest.spyOn(console, 'groupCollapsed').mockImplementation(() => {});
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'trace').mockImplementation(() => {});
    jest.spyOn(XMLHttpRequest.prototype, 'open').mockImplementation(function (method, url) {
      this.requestPath = new URL(url, window.location.origin).pathname;
    });
    jest.spyOn(XMLHttpRequest.prototype, 'setRequestHeader').mockImplementation(() => {});
    jest.spyOn(XMLHttpRequest.prototype, 'send').mockImplementation(function () {
      if (this.requestPath === '/api/content/contentnode/') {
        contentRequest = this;
        return;
      }
      const responses = {
        '/api/session/current/': session,
        '/api/classroom/classroom/': { id: 'classroom' },
        '/api/exam/quiz/': {
          id: 'quiz',
          data_model_version: 3,
          learners_see_fixed_order: true,
          question_sources: [
            {
              learners_see_fixed_order: true,
              questions: [{ exercise_id: 'exercise', question_id: 'question' }],
            },
          ],
        },
      };
      const data = responses[this.requestPath];
      if (!data) {
        throw new Error(`Unexpected request: ${this.requestPath}`);
      }
      if (this.requestPath === '/api/session/current/' && holdSessionRequest) {
        sessionRequest = this;
        return;
      }
      Object.defineProperties(this, {
        status: { value: 200 },
        responseText: { value: JSON.stringify(data) },
      });
      this.onloadend();
    });
  });

  afterEach(async () => {
    if (holdSessionRequest && sessionRequest) {
      sessionRequest.onerror();
      await flushPromises();
    }
    heartbeat.setReloadOnReconnect(false);
    holdSessionRequest = false;
    await heartbeat.pollSessionEndPoint();
    heartbeat.stopPolling();
    clearError();
    pageLoading.value = false;
    jest.restoreAllMocks();
  });

  async function openQuiz() {
    await heartbeat.startPolling();
    showExam(
      { commit: jest.fn() },
      { classId: 'classroom', examId: 'quiz', questionNumber: '0' },
      false,
      router.currentRoute,
    );
    await flushPromises();
    expect(pageLoading.value).toBe(true);
  }

  it('reports an HTTP 500 response', async () => {
    await openQuiz();
    Object.defineProperties(contentRequest, {
      status: { value: 500 },
      responseText: { value: JSON.stringify({ detail: 'Quiz content failed' }) },
    });
    contentRequest.onloadend();
    await flushPromises();

    expect(pageLoading.value).toBe(false);
    expect(JSON.parse(error.value)).toMatchObject({ status: 500 });
  });

  it('preserves the destination loader and avoids reloading on reconnect', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    await openQuiz();
    await router.push('/home');
    pageLoading.value = true;
    contentRequest.onerror();
    await flushPromises();

    expect(pageLoading.value).toBe(true);
    expect(error.value).toBeNull();

    heartbeat.monitorDisconnect();
    await heartbeat.pollSessionEndPoint();

    expect(router.currentRoute.fullPath).toBe('/home');
    expect(consoleError).not.toHaveBeenCalled();
  });

  it('attempts browser navigation when the session endpoint recovers', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    await openQuiz();
    holdSessionRequest = true;
    contentRequest.onerror();
    await flushPromises();

    expect(pageLoading.value).toBe(false);
    expect(error.value).toBeNull();
    expect(consoleError).not.toHaveBeenCalled();
    holdSessionRequest = false;
    sessionRequest.onerror();
    await flushPromises();
    await heartbeat.pollSessionEndPoint();

    expect(consoleError).toHaveBeenCalledTimes(1);
    expect(consoleError.mock.calls[0][0].message).toMatch(/Not implemented: navigation/);
  });
});
