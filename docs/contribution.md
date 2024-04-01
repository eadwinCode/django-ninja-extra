# **Contribution Guidelines**

Thank you for considering contributing to NinjaExtra! Your contributions help make the project better for everyone. 
Please take a moment to review the following guidelines before getting started.

## Setting up the Development Environment

1. **Fork the repository:** Fork the NinjaExtra repository on GitHub and clone it locally.

2. **Virtual Environment:** Create and activate a virtual environment for the project.

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. **Install `flit`:** Ensure you have `flit` installed globally.

   ```bash
   pip install flit
   ```

4. **Install Dependencies:** Install development libraries and pre-commit hooks.

   ```bash
   make install-full
   ```

### **Code Style and Formatting**

- **Formatting:** To format your code and ensure consistency, run:

  ```bash
  make fmt
  ```
  
- **Linting:** NinjaExtra uses `mypy` and `ruff` for linting. Run the following command to check code linting:

  ```bash
  make lint
  ```

### **Testing**

- **Unit Tests:** We use `pytest` for unit testing. Run the test suite:

  ```bash
  make test
  ```

- **Test Coverage:** To check test coverage:

  ```bash
  make test-cov
  ```

### **Submitting a Pull Request**

1. **Branch:** Create a new branch for your feature or bug fix.

   ```bash
   git checkout -b feature-branch
   ```

2. **Commit Messages:** Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for your commit messages.

3. **Push Changes:** Push your branch to your forked repository.

   ```bash
   git push origin feature-branch
   ```

4. **Pull Request:** Open a pull request against the `master` branch of the NinjaExtra repository. Provide a clear and descriptive title and description for your changes.


Thank you for contributing to NinjaExtra! 🚀
