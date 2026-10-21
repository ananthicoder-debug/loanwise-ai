/* ===================================================================
   LoanWise AI - API Configuration
   Backend deployed at: https://loanwise-ai-hem0.onrender.com
=================================================================== */

const PROD_API_URL  = "https://loanwise-ai-hem0.onrender.com";
const LOCAL_API_URL = "http://127.0.0.1:8000";

(function () {
  const h = window.location.hostname;
  const isLocal = (h === "localhost" || h === "127.0.0.1" || h === "" || h === "0.0.0.0");
  window._LOANWISE_API_URL = isLocal ? LOCAL_API_URL : PROD_API_URL;
})();
