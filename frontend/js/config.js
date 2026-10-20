/* ===================================================================
   LoanWise AI — config.js
   
   DEVELOPMENT:  Backend runs locally on http://127.0.0.1:8000
   PRODUCTION:   Update PROD_API_URL to your Render.com backend URL
                 after deploying the backend.
=================================================================== */

// Production backend URL (update this after deploying to Render.com)
const PROD_API_URL = "https://loanwise-ai-backend.onrender.com";

// Local development backend URL
const LOCAL_API_URL = "http://127.0.0.1:8000";

// Auto-detect: use production URL when not on localhost
(function() {
  const hostname = window.location.hostname;
  const isLocal  = (hostname === "localhost" ||
                    hostname === "127.0.0.1"  ||
                    hostname === ""            ||
                    hostname === "0.0.0.0");

  window._LOANWISE_API_URL = isLocal ? LOCAL_API_URL : PROD_API_URL;
})();
