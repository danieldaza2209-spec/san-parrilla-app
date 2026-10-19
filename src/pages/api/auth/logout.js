import { SESSION_COOKIE } from '../../../lib/auth.js';

export async function POST({ cookies, redirect }) {
  cookies.delete(SESSION_COOKIE, { path: '/' });
  return redirect('/login', 303);
}
