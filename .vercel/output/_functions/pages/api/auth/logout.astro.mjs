import { S as SESSION_COOKIE } from '../../../chunks/auth_CUmhD9Do.mjs';
export { renderers } from '../../../renderers.mjs';

async function POST({ cookies, redirect }) {
  cookies.delete(SESSION_COOKIE, { path: '/' });
  return redirect('/login', 303);
}

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  POST
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
