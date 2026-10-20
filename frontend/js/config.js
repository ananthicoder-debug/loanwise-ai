/* ===================================================================
   LoanWise AI - API Configuration
   
   LOCAL:       http://127.0.0.1:8000  (when running on your machine)
   PRODUCTION:  Your Render.com backend URL (update after deploying)
   
   HOW TO UPDATE FOR PRODUCTION:
   1. Deploy backend to Render.com (see DEPLOYMENT.md)
   2. Copy your Render URL (e.g. https://loanwise-ai-xyz.onrender.com)
   3. Paste it below replacing the PROD_API_URL value
   4. Re-upload frontend to Netlify
=================================================================== */

const PROD_API_URL  = "https://loanwise-ai-backend.onrender.com"; // UPDATE THIS after Render deploy
const LOCAL_API_URL = "http://127.0.0.1:8000";

(function () {
  const h = window.location.hostname;
  const isLocal = (h === "localhost" || h === "127.0.0.1" || h === "" || h === "0.0.0.0");
  window._LOANWISE_API_URL = isLocal ? LOCAL_API_URL : PROD_API_URL;
  console.log("[LoanWise AI] API:", window._LOANWISE_API_URL);
})();
