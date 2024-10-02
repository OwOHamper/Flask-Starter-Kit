<h1 align="center">
  <br>
  <a href="https://flaskstarter.com"">
    <img src="assets/logo.png" alt="Full-Stack Flask Starter Kit Logo" width=200 height=200>
  </a>
  <br>
  Full-Stack Flask Starter Kit
  <br>
</h1>

<h4 align="center">Quickly launch your web applications with the Full-Stack Flask Starter Kit.</h4>
<h5 align="center">
<a href="https://flaskstarter.com">
   Live Demo
</a>
</h5>

---

This project provides a streamlined setup for seamless development and deployment of Flask-based web applications, tailored to a specific workflow and preferences.

>This project is currently in its early stages of development. Much of the initial content has been generated with the assistance of AI to provide a starting point and placeholder text. As development progresses, this content will be reviewed and replaced to accurately represents the project's goals and functionality.

## 🌟 Key Features

1. **🚀 Easy Deployment**: Pre-configured Docker setup for straightforward deployment.
2. **🔐 Authentication System**: OAuth 2.0 support with email verification, password reset, and account linking.
3. **🔒 Security**: Robust security features including Content Security Policy (CSP) headers, CSRF protection, and more.
4. **📦 MongoDB Integration**: Fully integrated MongoDB support for scalable database management.
5. **🎨 Modern Design**: Utilizes Tailwind CSS and Flowbite UI library for a sleek, responsive design with light/dark mode support.
6. **🌐 Internationalization**: Babel integration for multi-language support.
7. **📊 SEO & Analytics**: Ready for search engine optimization and analytics integration.
8. **📄 Privacy Policy & ToS Templates**: Pre-made templates for legal compliance.
9. **🔔 Toast Notifications**: Manage notifications with a built-in toast notification system.
10. **🗜️ Optimization**: Automatic response minification and compression in production mode.
11. **🛡️ Rate Limiting**: Built-in rate limiting to protect against abuse.
12. **⚙️ Organized Project Structure**: Well-organized files and directories for easy navigation and maintenance.
13. **🐰 Celery & RabbitMQ Integration**: Ready integration of Celery with RabbitMQ for efficient task queuing and background processing.

## 🚧 Work in Progress / Planned Features

1. **💳 Stripe Integration**: Seamless payment processing with Stripe.
2. **📊 Admin Panel**: Interface for managing users and monitoring key metrics.
3. **📚 Documentation**: Comprehensive documentation for project setup, API endpoints, and usage guidelines.
4. **🎨 Animations & UI Improvements**: Enhancing user experience with smooth animations.
5. **🛠️ Project Generator** (Potential Feature): A CLI tool to generate new projects with pre-configured settings.


## 🚀 Quick Start

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flask-starter-kit.git
   cd flask-starter-kit
   ```

2. Set up a virtual environment
   ```bash
   python -m venv ./venv
   
   ./venv/Scripts/Active
   or (Depending on the operating system)
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   npm install
   ```

4. Compile tailwin classes
   ```bash
   .\tailwind.bat
   or (Depending on the operating system)
   ./tailwind.sh
   ```

5. Run the application:
   ```
   python server.py
   ```

6. Visit `http://localhost:5000` in your browser.

### Docker Setup

When deploying to production you should always use Docker or any similar deployment system.

1. Make sure you have Docker and Docker Compose installed.

2. Build and run the containers:
   ```bash
   docker-compose up --build -d
   ```

3. Visit `http://localhost:5000` in your browser.

4. (Optional) Access MongoDB Express at `http://localhost:8081` to manage your database.

### Babel Setup for Internationalization

To set up Babel for internationalization:

1. Extract translatable strings:
   ```
   pybabel extract -F babel.cfg -o messages.pot .
   ```

2. Create a new language catalog (e.g., for Spanish):
   ```
   pybabel init -i messages.pot -d translations -l es
   ```

3. Translate the strings in `translations/es/LC_MESSAGES/messages.po`

4. Compile the translations:
   ```
   pybabel compile -d translations
   ```

5. To update existing translations:
   ```
   pybabel update -i messages.pot -d translations
   ```

## 🎨 Customization

#### Color Customization
- Visit [uicolors](https://uicolors.app/create) and generate a pallete of your liking
- Export you colors and replace it with the `primary` color in the `tailwind.config.js`

## 🧩 Extending the Application

Add new routes in `server.py`, create corresponding templates, and implement additional functionality in the `src/` directory.

## 📝 TODO

The following features and improvements are planned for future development:

1. **👑 Admin Dashboard**: Develop an administrative interface for managing users and content.
2. **📊 Example Dashboard**: Build a sample dashboard showcasing data visualization and management capabilities.
3. **🧪 Unit Tests**: Develop a comprehensive suite of unit tests for core functionality.
4. **📈 User Activity Logging**: Add logging for important user actions and system events.
5. **📚 Documentation**: 
    - Create detailed documentation for the project setup and usage
    - Document API endpoints
    - Implement a robust search functionality across the documentation

We welcome contributions to any of these areas. If you're interested in working on one of these tasks, please open an issue to discuss it before submitting a pull request.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋 Support

For questions or assistance, please open an issue in the GitHub repository.

---

Built with a curated tech stack, tailored for efficiency and personal preference.

❤️ Crafted with passion using Flask, Tailwind CSS, and Flowbite.