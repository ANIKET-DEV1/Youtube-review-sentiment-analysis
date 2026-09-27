document.addEventListener('DOMContentLoaded', () => {
  const analyzerForm = document.getElementById('analyzerForm');
  const youtubeUrlInput = document.getElementById('youtubeUrl');
  const maxCommentsSelect = document.getElementById('maxComments');
  const submitBtn = document.getElementById('submitBtn');
  const btnText = document.getElementById('btnText');
  const btnSpinner = document.getElementById('btnSpinner');
  const demoBtn = document.getElementById('demoBtn');
  const errorBanner = document.getElementById('errorBanner');
  const errorMessage = document.getElementById('errorMessage');

  const resultsSection = document.getElementById('resultsSection');
  const totalCommentsVal = document.getElementById('totalCommentsVal');
  const overallBadge = document.getElementById('overallBadge');
  const overallBadgeText = document.getElementById('overallBadgeText');
  const posPercentVal = document.getElementById('posPercentVal');
  const negPercentVal = document.getElementById('negPercentVal');

  const posCountText = document.getElementById('posCountText');
  const negCountText = document.getElementById('negCountText');
  const neuCountText = document.getElementById('neuCountText');

  const posBar = document.getElementById('posBar');
  const negBar = document.getElementById('negBar');
  const neuBar = document.getElementById('neuBar');

  const commentsList = document.getElementById('commentsList');
  const filterBtns = document.querySelectorAll('.filter-btn[data-filter]');

  let allPredictions = [];

  // Demo URL handler
  demoBtn.addEventListener('click', () => {
    youtubeUrlInput.value = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    analyzerForm.dispatchEvent(new Event('submit'));
  });

  // Form submit handler
  analyzerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = youtubeUrlInput.value.trim();
    const maxComments = parseInt(maxCommentsSelect.value, 10);

    if (!url) return;

    // Reset UI
    showLoading(true);
    hideError();
    resultsSection.classList.add('hidden');

    try {
      const response = await fetch('/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, max_comments: maxComments })
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'success' && data.sentiment_analysis) {
        renderResults(data);
      } else {
        showError(data.warning || 'Failed to analyze video comments.');
      }

    } catch (err) {
      console.error('API Error:', err);
      showError(`Error connecting to server: ${err.message}`);
    } finally {
      showLoading(false);
    }
  });

  // Render Analysis Results
  function renderResults(data) {
    const analysis = data.sentiment_analysis;
    const summary = analysis.summary || { positive: 0, negative: 0, neutral: 0 };
    const percentage = analysis.percentage || { positive: 0, negative: 0, neutral: 0 };
    const overall = analysis.overall_sentiment || 'neutral';
    allPredictions = analysis.predictions || [];

    // Metrics
    totalCommentsVal.textContent = analysis.total_comments;

    // Overall Badge
    overallBadge.className = `badge-overall badge-${overall}`;
    overallBadgeText.textContent = overall;

    // Percentages
    posPercentVal.textContent = `${percentage.positive}%`;
    negPercentVal.textContent = `${percentage.negative}%`;

    // Counts & Breakdown Text
    posCountText.textContent = `${summary.positive} comments (${percentage.positive}%)`;
    negCountText.textContent = `${summary.negative} comments (${percentage.negative}%)`;
    neuCountText.textContent = `${summary.neutral} comments (${percentage.neutral}%)`;

    // Progress Bars
    posBar.style.width = `${percentage.positive}%`;
    negBar.style.width = `${percentage.negative}%`;
    neuBar.style.width = `${percentage.neutral}%`;

    // Render Comments List
    renderComments('all');

    // Show Results Section
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
  }

  // Render Filtered Comments
  function renderComments(filter = 'all') {
    commentsList.innerHTML = '';

    const filtered = allPredictions.filter(item => {
      if (filter === 'all') return true;
      return item.sentiment.toLowerCase() === filter;
    });

    if (filtered.length === 0) {
      commentsList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No ${filter} comments found.</div>`;
      return;
    }

    filtered.forEach((item, index) => {
      const card = document.createElement('div');
      card.className = 'comment-card';

      const sentimentClass = `badge-${item.sentiment.toLowerCase()}`;

      card.innerHTML = `
        <div class="comment-text">"${escapeHtml(item.text)}"</div>
        <div class="comment-right">
          <span class="badge-overall ${sentimentClass}">${escapeHtml(item.sentiment)}</span>
          <button class="btn-feedback" onclick="submitFeedbackPrompt('${escapeJsString(item.text)}', '${item.sentiment}')">
            ✏️ Correct
          </button>
        </div>
      `;
      commentsList.appendChild(card);
    });
  }

  // Filter Buttons Event
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.getAttribute('data-filter');
      renderComments(filter);
    });
  });

  // UI Helpers
  function showLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      btnText.textContent = 'Scraping & Analyzing...';
      btnSpinner.classList.remove('hidden');
    } else {
      submitBtn.disabled = false;
      btnText.textContent = 'Analyze Video';
      btnSpinner.classList.add('hidden');
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove('hidden');
  }

  function hideError() {
    errorBanner.classList.add('hidden');
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function escapeJsString(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
  }

  // Global inline feedback function
  window.submitFeedbackPrompt = async function(commentText, currentSentiment) {
    const newSentiment = prompt(
      `Correction for:\n"${commentText}"\n\nCurrent prediction: ${currentSentiment}\n\nEnter corrected sentiment (positive, negative, neutral):`,
      currentSentiment
    );

    if (!newSentiment) return;
    const cleanSentiment = newSentiment.trim().toLowerCase();

    if (!['positive', 'negative', 'neutral'].includes(cleanSentiment)) {
      alert('Invalid sentiment! Must be positive, negative, or neutral.');
      return;
    }

    try {
      const res = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          comment: commentText,
          sentiment: cleanSentiment
        })
      });
      const data = await res.json();
      if (res.ok) {
        alert('Feedback submitted successfully! Thank you for helping retrain the model.');
      } else {
        alert(`Error: ${data.detail || 'Failed to submit feedback'}`);
      }
    } catch (e) {
      alert(`Network error: ${e.message}`);
    }
  };
});
