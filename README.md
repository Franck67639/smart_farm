<<<<<<< HEAD
# 🌱 Smart Farm

**Smart Farm** is an **AI‑powered web application** designed to boost agricultural productivity in **Cameroon** and similar regions by helping farmers make smarter, data‑driven decisions.

The platform combines **artificial intelligence, weather insights, and modern web technologies** to support farmers with crop monitoring, decision support, and sustainable farming practices.

---

## 🚀 Project Vision

Agriculture is the backbone of Cameroon’s economy, yet many farmers still rely on traditional methods that are vulnerable to climate change, pests, and inefficient resource use.

**Smart Farm aims to:**

* Improve crop yield and food security
* Reduce losses caused by climate variability
* Promote modern, data‑driven farming
* Make technology accessible to local farmers

---

## 🧠 Key Features

* 🌦️ **AI‑Assisted Weather Insights** – Helps farmers anticipate weather conditions and plan accordingly
* 🌾 **Crop Management Support** – Recommendations for planting, irrigation, and harvesting
* 📊 **Data‑Driven Decision Making** – Uses analytics to optimize agricultural practices
* 🧑‍🌾 **Farmer‑Friendly Interface** – Simple and intuitive design adapted for local use
* 🌍 **Localized for Cameroon** – Focused on local crops, climate, and farming realities

---

## 🛠️ Tech Stack

* **Backend:** Python (Django)
* **Frontend:** HTML, CSS, JavaScript
* **AI / Logic:** Machine learning & rule‑based decision support
* **Database:** SQLite / PostgreSQL (depending on deployment)
* **APIs:** Weather & agricultural data APIs

---

## 👨‍💻 About the Developer

**Franck Assontia (Assontia Franck Junior)**
🎓 Software Engineering Student
💻 Passionate about web development, AI, and real-world problem solving
🌍 Focused on building technology that creates impact in Africa

📧 **Email:** [franckassontia6@gmail.com](mailto:franckassontia6@gmail.com)
📞 **Phone:** +237 652 352 815

I enjoy working on projects that combine **software engineering and social impact**, especially in areas like **agriculture, education, and enterprise solutions**.

---

## 🎯 Project Goals

* Provide affordable smart farming tools
* Support small‑scale farmers
* Encourage digital transformation in agriculture
* Serve as a foundation for future AI‑driven agricultural systems

---

## 📌 Current Status

🚧 **Under active development**
Features and models are continuously being improved.

---

## 🤝 Contributions

Contributions, ideas, and feedback are welcome!

If you would like to contribute:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is released for **educational and research purposes**. Licensing details can be updated later.

---

## ⭐ Support

If you find this project useful or inspiring, please consider giving it a **star ⭐** on GitHub.

Together, let’s build smarter solutions for agriculture 🌱
=======
# SmartFarm - Premium Maize Farming Web Application

A beautiful, mobile-first Django web application designed specifically for maize farmers in Cameroon/Douala region.

## Features

### 🌱 Core Functionality
- **Smart Onboarding**: 7-step guided setup with location detection, soil analysis, and variety selection
- **Weather Dashboard**: Real-time weather data with 7-day forecasts and hourly updates
- **Personalized Recommendations**: AI-driven farming advice based on local conditions
- **Farm Management**: Track multiple farms, soil conditions, and crop progress

### 🎨 Design System
- **Dark Mode First**: Premium forest-themed aesthetic with mint accents
- **Glassmorphism**: Modern frosted glass effects with backdrop blur
- **Mobile-First**: Responsive design optimized for smartphones and tablets
- **Micro-interactions**: Smooth transitions and hover states throughout

### 🛠 Technical Stack
- **Backend**: Django 6.x with SQLite
- **Frontend**: 100% server-side rendered templates (no React/Vue)
- **Styling**: Tailwind CSS via CDN (v4.x)
- **Interactivity**: HTMX + Alpine.js for dynamic content
- **Icons**: Lucide icons via CDN
- **Typography**: Inter font family

## Project Structure

```
smart_farm/
├── templates/
│   ├── base.html                 # Main template with all CDNs
│   ├── dashboard.html            # Main dashboard view
│   ├── auth/
│   │   └── login.html           # Login screen with glass card
│   └── partials/
│       ├── _onboarding_step1.html  # Welcome screen
│       ├── _onboarding_step2.html  # Maize variety selection
│       ├── _onboarding_step3.html  # Location detection
│       ├── _onboarding_step4.html  # Farm details
│       ├── _onboarding_step5.html  # Soil information
│       ├── _onboarding_step6.html  # Growing preferences
│       ├── _onboarding_step7.html  # Setup complete
│       ├── _weather_widget.html     # Weather dashboard
│       └── _recommendations.html   # Smart recommendations
├── smart_farm/
│   ├── settings.py              # Django configuration
│   ├── urls.py                  # URL routing
│   └── views.py                 # View functions
└── manage.py
```

## Getting Started

### Prerequisites
- Python 3.8+
- Django 6.x

### Installation

1. **Clone and setup**
```bash
cd smart_farm
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install django
```

2. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create superuser (optional)**
```bash
python manage.py createsuperuser
```

4. **Start development server**
```bash
python manage.py runserver
```

5. **Access the application**
- Main app: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: http://127.0.0.1:8000/login/

## Key Features Explained

### 🌿 Onboarding Flow
1. **Welcome**: Animated introduction with feature preview
2. **Maize Variety**: Visual selection with search or image grid
3. **Location Detection**: GPS-based farm location with accuracy indicators
4. **Farm Details**: Name, size, type configuration
5. **Soil Analysis**: Visual soil type selection with pH slider
6. **Growing Preferences**: Season, irrigation, experience level
7. **Complete**: Summary with confetti animation

### 🌤️ Weather Dashboard
- Current conditions with large temperature display
- Hourly forecast with scrollable timeline
- 7-day forecast with rain probability
- Auto-refresh every 30 minutes via HTMX
- Detailed metrics (wind, humidity, UV index)

### 💡 Smart Recommendations
- **Sowing Window**: Optimal planting timing with success rates
- **Weather Alerts**: Rain warnings and extreme weather
- **Fertilizer Advice**: NPK recommendations based on soil
- **Market Prices**: Real-time price trends and profit estimates
- **Pest Warnings**: Regional pest alerts and treatment guides

### 🎯 Design Highlights
- **Glass Cards**: `backdrop-blur-xl bg-black/30 border border-white/10`
- **Color Palette**: Forest greens (#051F20 to #235347) with mint accents
- **Typography**: Inter font with proper weight hierarchy
- **Animations**: Float effects, pulse animations, smooth transitions
- **Responsive**: Mobile-first with Tailwind breakpoints

## URL Structure

- `/` - Main dashboard (requires login)
- `/login/` - User authentication
- `/register/` - User registration
- `/logout/` - User logout
- `/onboarding/step/<n>/` - Onboarding steps 1-7
- `/weather/partial/` - HTMX weather widget updates
- `/api/set-farm/` - Farm switching API

## Custom Components

### Alpine.js Components
- `farmSwitcher`: Multi-farm management dropdown
- `notifications`: Real-time notification system
- `locationDetector`: GPS-based location capture
- `maizeSelector`: Interactive variety selection

### HTMX Integration
- Auto-refreshing weather data
- Partial template swaps for onboarding
- Form submissions without page reloads
- API endpoints for dynamic content

## Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Features
- CDN-delivered assets (no build process)
- Optimized images with lazy loading
- Minimal JavaScript footprint
- Server-side rendering for fast initial load

## Future Enhancements
- [ ] Push notifications for weather alerts
- [ ] Offline PWA functionality
- [ ] Advanced analytics dashboard
- [ ] Integration with local weather stations
- [ ] Mobile app (React Native)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

---

**SmartFarm** - Empowering Cameroon's maize farmers with technology 🌽🌿
>>>>>>> 00bc0ae (Initial commit)
