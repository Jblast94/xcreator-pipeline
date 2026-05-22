// XCreator Pro - Main JavaScript File
// Handles all interactive functionality, animations, and data visualization

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    // Initialize common components
    initializeNavigation();
    initializeAnimations();
    
    // Page-specific initialization
    const currentPage = getCurrentPage();
    switch(currentPage) {
        case 'index':
            initializeLandingPage();
            break;
        case 'dashboard':
            initializeDashboard();
            break;
        case 'content-studio':
            initializeContentStudio();
            break;
        case 'monetization':
            initializeMonetization();
            break;
    }
}

// Get current page from URL
function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('dashboard')) return 'dashboard';
    if (path.includes('content-studio')) return 'content-studio';
    if (path.includes('monetization')) return 'monetization';
    return 'index';
}

// Navigation functionality
function initializeNavigation() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('-translate-x-full');
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 1024 && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
            sidebar.classList.add('-translate-x-full');
        }
    });
}

// Animation initialization
function initializeAnimations() {
    // Animate metric cards on scroll
    const metricCards = document.querySelectorAll('.metric-card, .revenue-card');
    if (metricCards.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    anime({
                        targets: entry.target,
                        translateY: [20, 0],
                        opacity: [0, 1],
                        duration: 600,
                        easing: 'easeOutCubic',
                        delay: Math.random() * 200
                    });
                }
            });
        });
        
        metricCards.forEach(card => observer.observe(card));
    }
}

// Landing Page Initialization
function initializeLandingPage() {
    // Typewriter effect for hero text
    if (document.getElementById('typed-text')) {
        const typed = new Typed('#typed-text', {
            strings: ['Audience', 'Revenue', 'Influence', 'Brand'],
            typeSpeed: 100,
            backSpeed: 50,
            backDelay: 2000,
            loop: true,
            showCursor: true,
            cursorChar: '|'
        });
    }
    
    // Initialize testimonials slider
    if (document.getElementById('testimonials-slider')) {
        new Splide('#testimonials-slider', {
            type: 'loop',
            perPage: 2,
            perMove: 1,
            gap: '2rem',
            autoplay: true,
            interval: 5000,
            breakpoints: {
                768: {
                    perPage: 1,
                }
            }
        }).mount();
    }
    
    // Initialize growth chart
    initializeGrowthChart();
    
    // Animate metrics on scroll
    animateLandingMetrics();
}

// Dashboard Initialization
function initializeDashboard() {
    // Initialize charts
    initializeDashboardCharts();
    
    // Animate metric counters
    animateMetricCounters();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
}

// Content Studio Initialization
function initializeContentStudio() {
    // Content type selector
    initializeContentTypeSelector();
    
    // Character counter
    initializeCharacterCounter();
    
    // AI content generation
    initializeAIContentGeneration();
    
    // Hashtag suggestions
    initializeHashtagSuggestions();
    
    // Content calendar interactions
    initializeContentCalendar();
}

// Monetization Initialization
function initializeMonetization() {
    // Initialize revenue chart
    initializeRevenueChart();
    
    // Rate calculator
    initializeRateCalculator();
    
    // Brand compatibility animations
    initializeBrandCompatibility();
}

// Chart Initialization Functions
function initializeGrowthChart() {
    const chartElement = document.getElementById('growth-chart');
    if (!chartElement) return;
    
    const chart = echarts.init(chartElement);
    
    const option = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e5e7eb',
            textStyle: {
                color: '#374151'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
            axisLine: {
                lineStyle: {
                    color: '#e5e7eb'
                }
            },
            axisLabel: {
                color: '#6b7280'
            }
        },
        yAxis: {
            type: 'value',
            axisLine: {
                lineStyle: {
                    color: '#e5e7eb'
                }
            },
            axisLabel: {
                color: '#6b7280'
            },
            splitLine: {
                lineStyle: {
                    color: '#f3f4f6'
                }
            }
        },
        series: [{
            name: 'Followers',
            type: 'line',
            data: [45, 52, 61, 73, 89, 108, 125, 142, 165, 189, 210],
            smooth: true,
            lineStyle: {
                color: '#3b82f6',
                width: 3
            },
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [{
                        offset: 0,
                        color: 'rgba(59, 130, 246, 0.3)'
                    }, {
                        offset: 1,
                        color: 'rgba(59, 130, 246, 0.05)'
                    }]
                }
            },
            itemStyle: {
                color: '#3b82f6'
            }
        }]
    };
    
    chart.setOption(option);
    
    // Animate chart on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                chart.resize();
            }
        });
    });
    observer.observe(chartElement);
}

function initializeDashboardCharts() {
    // Growth Chart
    const growthChart = echarts.init(document.getElementById('growth-chart'));
    const growthOption = {
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: ['Followers', 'Engagement']
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        },
        yAxis: [
            {
                type: 'value',
                name: 'Followers',
                position: 'left'
            },
            {
                type: 'value',
                name: 'Engagement %',
                position: 'right'
            }
        ],
        series: [
            {
                name: 'Followers',
                type: 'bar',
                data: [120, 125, 128, 132],
                itemStyle: {
                    color: '#3b82f6'
                }
            },
            {
                name: 'Engagement',
                type: 'line',
                yAxisIndex: 1,
                data: [7.2, 8.1, 8.5, 8.7],
                itemStyle: {
                    color: '#8b5cf6'
                }
            }
        ]
    };
    growthChart.setOption(growthOption);
    
    // Engagement Chart
    const engagementChart = echarts.init(document.getElementById('engagement-chart'));
    const engagementOption = {
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: ['Likes', 'Comments', 'Shares']
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        },
        yAxis: {
            type: 'value'
        },
        series: [
            {
                name: 'Likes',
                type: 'line',
                data: [1200, 1350, 1100, 1800, 1600, 1400, 1900],
                itemStyle: {
                    color: '#3b82f6'
                }
            },
            {
                name: 'Comments',
                type: 'line',
                data: [180, 220, 150, 320, 280, 200, 350],
                itemStyle: {
                    color: '#8b5cf6'
                }
            },
            {
                name: 'Shares',
                type: 'line',
                data: [320, 380, 280, 450, 400, 350, 480],
                itemStyle: {
                    color: '#10b981'
                }
            }
        ]
    };
    engagementChart.setOption(engagementOption);
}

function initializeRevenueChart() {
    const chartElement = document.getElementById('revenue-chart');
    if (!chartElement) return;
    
    const chart = echarts.init(chartElement);
    
    const option = {
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                return params.map(param => 
                    `${param.seriesName}: $${param.value.toLocaleString()}`
                ).join('<br/>');
            }
        },
        legend: {
            data: ['Brand Partnerships', 'Subscriptions', 'Digital Products']
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '${value}'
            }
        },
        series: [
            {
                name: 'Brand Partnerships',
                type: 'bar',
                stack: 'total',
                data: [1200, 1800, 2100, 2800, 3200, 3400],
                itemStyle: {
                    color: '#3b82f6'
                }
            },
            {
                name: 'Subscriptions',
                type: 'bar',
                stack: 'total',
                data: [400, 600, 800, 1000, 1200, 1280],
                itemStyle: {
                    color: '#8b5cf6'
                }
            },
            {
                name: 'Digital Products',
                type: 'bar',
                stack: 'total',
                data: [200, 300, 400, 500, 600, 680],
                itemStyle: {
                    color: '#10b981'
                }
            }
        ]
    };
    
    chart.setOption(option);
}

// Content Studio Functions
function initializeContentTypeSelector() {
    const buttons = document.querySelectorAll('.content-type-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            buttons.forEach(btn => {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('bg-gray-200', 'text-gray-700');
            });
            
            // Add active class to clicked button
            this.classList.remove('bg-gray-200', 'text-gray-700');
            this.classList.add('bg-blue-600', 'text-white');
            
            // Update content based on selection
            updateContentEditor(this.id);
        });
    });
}

function updateContentEditor(buttonId) {
    const editor = document.getElementById('content-editor');
    const placeholderText = {
        'single-tweet-btn': 'What\'s happening? Share your thoughts...',
        'thread-btn': 'Start your thread with the first tweet...',
        'image-post-btn': 'Describe your visual content...'
    };
    
    if (editor && placeholderText[buttonId]) {
        editor.placeholder = placeholderText[buttonId];
    }
}

function initializeCharacterCounter() {
    const editor = document.getElementById('content-editor');
    const counter = document.getElementById('char-count');
    
    if (editor && counter) {
        editor.addEventListener('input', function() {
            const length = this.value.length;
            const maxLength = this.getAttribute('maxlength');
            counter.textContent = `${length}/${maxLength}`;
            
            // Change color based on usage
            if (length > maxLength * 0.9) {
                counter.classList.add('text-red-500');
                counter.classList.remove('text-gray-500');
            } else if (length > maxLength * 0.7) {
                counter.classList.add('text-yellow-500');
                counter.classList.remove('text-gray-500', 'text-red-500');
            } else {
                counter.classList.add('text-gray-500');
                counter.classList.remove('text-yellow-500', 'text-red-500');
            }
        });
    }
}

function initializeAIContentGeneration() {
    const generateBtn = document.getElementById('generate-content-btn');
    const optimizeBtn = document.getElementById('optimize-content-btn');
    const editor = document.getElementById('content-editor');
    
    if (generateBtn && editor) {
        generateBtn.addEventListener('click', function() {
            generateAIContent();
        });
    }
    
    if (optimizeBtn && editor) {
        optimizeBtn.addEventListener('click', function() {
            optimizeContent();
        });
    }
}

function generateAIContent() {
    const editor = document.getElementById('content-editor');
    const sampleContent = [
        '🚀 AI is transforming content creation! Here are 5 ways to leverage AI tools for better engagement: 1) Automate repetitive tasks 2) Generate data-driven insights 3) Optimize posting times 4) Create personalized content 5) Analyze performance metrics. What\'s your favorite AI tool? 👇',
        '💡 Pro tip: Your engagement rate matters more than your follower count. Focus on creating valuable content that sparks conversations. Quality over quantity always wins in the long run. What content gets the most engagement from your audience?',
        '🎯 The future of social media is AI-powered personalization. Brands that adapt will thrive, those that don\'t will fade away. Are you ready for the AI revolution in content creation? Share your thoughts below! 🧠✨'
    ];
    
    const randomContent = sampleContent[Math.floor(Math.random() * sampleContent.length)];
    
    // Animate content generation
    editor.style.opacity = '0.5';
    setTimeout(() => {
        editor.value = randomContent;
        editor.style.opacity = '1';
        
        // Trigger character counter update
        editor.dispatchEvent(new Event('input'));
        
        // Update performance prediction
        updatePerformancePrediction();
    }, 1000);
    
    // Show generation animation
    showAIGenerationAnimation();
}

function optimizeContent() {
    const editor = document.getElementById('content-editor');
    if (!editor || !editor.value) return;
    
    // Simulate optimization
    editor.style.opacity = '0.5';
    setTimeout(() => {
        let content = editor.value;
        
        // Add optimized hashtags
        const optimizedHashtags = ['#ContentStrategy', '#AITools', '#SocialMediaGrowth', '#CreatorTips'];
        content += '\\n\\n' + optimizedHashtags.join(' ');
        
        editor.value = content;
        editor.style.opacity = '1';
        editor.dispatchEvent(new Event('input'));
        
        // Show success message
        showOptimizationSuccess();
    }, 1500);
}

function showAIGenerationAnimation() {
    const button = document.getElementById('generate-content-btn');
    const originalText = button.innerHTML;
    
    button.innerHTML = `
        <svg class="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        <span>Generating...</span>
    `;
    
    setTimeout(() => {
        button.innerHTML = originalText;
    }, 1000);
}

function showOptimizationSuccess() {
    // Create temporary success message
    const successMsg = document.createElement('div');
    successMsg.className = 'fixed top-20 right-6 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
    successMsg.textContent = 'Content optimized successfully!';
    
    document.body.appendChild(successMsg);
    
    setTimeout(() => {
        successMsg.remove();
    }, 3000);
}

function updatePerformancePrediction() {
    const predictions = {
        engagement: (Math.random() * 5 + 8).toFixed(1) + '%',
        reach: Math.floor(Math.random() * 20000 + 30000),
        viral: Math.floor(Math.random() * 5) + 1
    };
    
    // Update DOM elements if they exist
    const engagementElement = document.querySelector('.ai-suggestion .text-blue-600');
    const reachElement = document.querySelector('.ai-suggestion .text-green-600');
    
    if (engagementElement) engagementElement.textContent = predictions.engagement;
    if (reachElement) reachElement.textContent = predictions.reach.toLocaleString() + 'K';
}

function initializeHashtagSuggestions() {
    const hashtagContainer = document.getElementById('hashtag-container');
    if (!hashtagContainer) return;
    
    const hashtags = hashtagContainer.querySelectorAll('.hashtag-tag');
    hashtags.forEach(tag => {
        tag.addEventListener('click', function() {
            const editor = document.getElementById('content-editor');
            if (editor) {
                editor.value += ' ' + this.textContent;
                editor.dispatchEvent(new Event('input'));
            }
        });
    });
}

function initializeContentCalendar() {
    const calendarDays = document.querySelectorAll('.calendar-day');
    calendarDays.forEach(day => {
        day.addEventListener('click', function() {
            // Show scheduling modal or form
            showSchedulingForm(this);
        });
    });
}

function showSchedulingForm(dayElement) {
    // Create a simple scheduling form
    const date = dayElement.querySelector('.text-sm.font-medium').textContent;
    
    const form = document.createElement('div');
    form.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    form.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 class="text-lg font-semibold mb-4">Schedule Post for ${date}</h3>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Time</label>
                    <input type="time" class="w-full border border-gray-300 rounded-lg px-3 py-2" value="09:00">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Content</label>
                    <textarea class="w-full border border-gray-300 rounded-lg px-3 py-2 h-24" placeholder="Post content..."></textarea>
                </div>
                <div class="flex space-x-3">
                    <button class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">Schedule</button>
                    <button class="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-50" onclick="this.closest('.fixed').remove()">Cancel</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(form);
}

// Monetization Functions
function initializeRateCalculator() {
    const inputs = document.querySelectorAll('.rate-calculator input, .rate-calculator select');
    inputs.forEach(input => {
        input.addEventListener('change', calculateRecommendedRate);
    });
}

function calculateRecommendedRate() {
    const followers = parseInt(document.querySelector('.rate-calculator input[type="number"]').value) || 0;
    const engagementRate = parseFloat(document.querySelector('.rate-calculator input[step="0.1"]').value) || 0;
    const contentType = document.querySelector('.rate-calculator select').value;
    
    // Simple rate calculation formula
    let baseRate = (followers / 1000) * engagementRate * 10;
    
    // Content type multiplier
    const multipliers = {
        'Single Post': 1,
        'Thread (3-5 tweets)': 1.5,
        'Video Content': 2,
        'Story Series': 1.2
    };
    
    const recommendedRate = Math.round(baseRate * (multipliers[contentType] || 1));
    
    const resultElement = document.querySelector('.rate-calculator .text-green-600');
    if (resultElement) {
        resultElement.textContent = '$' + recommendedRate.toLocaleString();
    }
}

function initializeBrandCompatibility() {
    const compatibilityBars = document.querySelectorAll('.compatibility-bar');
    compatibilityBars.forEach(bar => {
        const indicator = bar.querySelector('.compatibility-indicator');
        const percentage = parseInt(indicator.style.left);
        
        // Animate the indicator
        anime({
            targets: indicator,
            left: '0%',
            duration: 0,
            complete: function() {
                anime({
                    targets: indicator,
                    left: percentage + '%',
                    duration: 1500,
                    easing: 'easeOutCubic'
                });
            }
        });
    });
}

// Utility Functions
function animateMetricCounters() {
    const counters = document.querySelectorAll('[id$="-count"], [id$="-rate"], [id$="-revenue"]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent.replace(/[^0-9]/g, ''));
        const suffix = counter.textContent.replace(/[0-9]/g, '');
        
        anime({
            targets: { value: 0 },
            value: target,
            duration: 2000,
            easing: 'easeOutCubic',
            update: function(anim) {
                const currentValue = Math.round(anim.animatables[0].target.value);
                counter.textContent = currentValue.toLocaleString() + suffix;
            }
        });
    });
}

function animateLandingMetrics() {
    const metrics = document.querySelectorAll('.text-2xl.font-bold');
    metrics.forEach(metric => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    anime({
                        targets: entry.target,
                        scale: [0.8, 1],
                        opacity: [0, 1],
                        duration: 800,
                        easing: 'easeOutElastic(1, .8)'
                    });
                }
            });
        });
        observer.observe(metric);
    });
}

function initializeRealTimeUpdates() {
    // Simulate real-time metric updates
    setInterval(() => {
        updateMetrics();
    }, 30000); // Update every 30 seconds
}

function updateMetrics() {
    const metrics = {
        'total-followers': Math.floor(Math.random() * 100 + 125700),
        'engagement-rate': (Math.random() * 2 + 8).toFixed(1) + '%',
        'monthly-reach': Math.floor(Math.random() * 5000 + 450000),
        'monthly-revenue': '$' + (Math.floor(Math.random() * 500 + 4600)).toLocaleString()
    };
    
    Object.entries(metrics).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
});

// Resize handler for charts
window.addEventListener('resize', function() {
    // Resize all ECharts instances
    const charts = document.querySelectorAll('[id$="-chart"]');
    charts.forEach(chartElement => {
        const chartInstance = echarts.getInstanceByDom(chartElement);
        if (chartInstance) {
            chartInstance.resize();
        }
    });
});

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeApp,
        generateAIContent,
        calculateRecommendedRate,
        updatePerformancePrediction
    };
}