<h1 align="center">
  <br>
  <a href="https://example.com/">
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

## 🌟 Key Features

1. **🚀 Easy Deployment**: Pre-configured Docker setup for straightforward deployment.
2. **🎨 Modern Design**: Utilizes Tailwind CSS and Flowbite UI library for enhanced design capabilities.
3. **🔒 Security**: Implements Talisman for security headers and ProxyFix for proper handling of proxies.
4. **🗜️ Optimization**: Automatic response minification and compression in production mode.
5. **🛡️ Rate Limiting**: Built-in rate limiting to protect against abuse.

## 💡 Additional Features

- **🌓 Theme Switcher**: Built-in dark mode support for better user experience.
- **🌐 Internationalization**: Babel integration for multi-language support.
- **📊 SEO & Analytics**: Ready for search engine optimization and analytics integration.

## 🧰 About This Stack

This Flask Starter Kit is built with a specific set of tools and technologies that, while not universally perfect, align well with certain development preferences and workflows. It's designed to be a pragmatic solution for those who find this particular combination of technologies efficient and effective.

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
   #KEEP in mind this won't build tailwind styles, you will need to build them beforehand
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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋 Support

For questions or assistance, please open an issue in the GitHub repository.

---

Built with a curated tech stack, tailored for efficiency and personal preference.

❤️ Crafted with passion using Flask, Tailwind CSS, and Flowbite.