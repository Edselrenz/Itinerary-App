# MASTER PROMPT: Build a Python Flet Desktop Application for My Existing Web Application

## ROLE

Act as a Senior Python Developer, Desktop Application Engineer, Software Architect, UI/UX Designer, Backend Integration Engineer, and Quality Assurance Engineer.

Your task is to develop a fully functional desktop application using **Python Flet** that integrates with my existing web application.

You have access to my development workspace through Antigravity. You must inspect the existing project, understand its architecture, and develop a desktop application that works with the same backend, database, authentication system, and business logic wherever possible.

This is an actual development task, not a request for a tutorial, concept, or demonstration.

Do not stop after analyzing the project or generating a development plan. Proceed with implementation, execution, debugging, testing, and documentation.

---

# 1. PRIMARY OBJECTIVE

Create a native-feeling desktop application using Python Flet that provides desktop access to the functionality of my existing web application.

The desktop application must:

- Work independently as a desktop program.
- Communicate with the existing backend through its APIs.
- Reuse the existing database and backend business logic.
- Maintain compatibility with the existing web application.
- Provide a desktop-optimized user interface.
- Support the important features and workflows already available in the web application.
- Be structured so that future updates and additional features are easy to implement.
- Be buildable into a distributable desktop executable.

The existing web application must remain functional and must not be broken, replaced, or unnecessarily rewritten.

## Important architectural requirement

Do not simply place my existing website inside a WebView and call it a desktop application.

Build an actual desktop interface using Flet components.

The Flet application should function as a separate client that communicates with the existing backend.

---

# 2. PHASE 1 — INSPECT AND UNDERSTAND THE EXISTING PROJECT

Before writing any code, thoroughly inspect the entire existing project.

Identify and document:

1. Existing frontend framework and architecture.
2. Backend framework and architecture.
3. Database technology and database structure.
4. Available API endpoints.
5. Authentication and authorization mechanisms.
6. User roles and permissions.
7. Existing application modules and features.
8. Business rules and validation logic.
9. Third-party APIs and integrations.
10. Existing environment variables and configuration.
11. Existing deployment architecture.
12. Existing file storage and upload mechanisms.
13. Important dependencies and their versions.

Inspect relevant source files, configuration files, database models, API routes, services, and documentation.

Do not assume that the application works in a particular way without verifying it through the source code.

### Produce an architecture assessment

Create:

`DESKTOP_APP_DOCUMENTATION/01_EXISTING_SYSTEM_ANALYSIS.md`

Include:

- Existing system architecture.
- Existing technology stack.
- Database and backend relationships.
- Authentication flow.
- Available API endpoints.
- Existing application features.
- External integrations.
- Limitations and potential integration problems.
- Recommended desktop application architecture.

### Feature mapping

Create:

`DESKTOP_APP_DOCUMENTATION/02_FEATURE_MAPPING.md`

Prepare a feature comparison table containing:

| Existing Web Feature | Desktop Implementation | Backend Integration | Status |
|---|---|---|---|
| Feature name | How it will work on desktop | API endpoint/service | Pending |

Identify every important feature that should be available in the desktop application.

Do not overlook secondary features such as account settings, profile management, notifications, search, filters, and other supporting workflows.

---

# 3. PHASE 2 — DESIGN THE DESKTOP ARCHITECTURE

Use Python Flet as the primary desktop application framework.

Design a modular architecture that separates the user interface, business logic, backend communication, authentication, and application configuration.

Use an appropriate structure similar to the following, adapting it to the actual requirements:

```text
desktop_client/
│
├── main.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── fonts/
│
├── config/
│   ├── settings.py
│   └── environment.py
│
├── core/
│   ├── api_client.py
│   ├── exceptions.py
│   ├── session.py
│   └── utilities.py
│
├── models/
│   ├── user.py
│   └── application_models.py
│
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   └── application_services.py
│
├── components/
│   ├── navigation.py
│   ├── sidebar.py
│   ├── dialogs.py
│   └── reusable_components.py
│
├── views/
│   ├── login_view.py
│   ├── dashboard_view.py
│   ├── settings_view.py
│   └── application_views.py
│
├── tests/
│   ├── test_api_client.py
│   ├── test_auth.py
│   └── test_services.py
│
└── documentation/
```

This is a proposed structure, not a rigid requirement. Adapt it based on the actual size and complexity of the application.

### Architectural rules

- Keep UI components separate from backend communication.
- Avoid placing all application logic inside `main.py`.
- Use reusable components.
- Use proper Python type hints where appropriate.
- Handle asynchronous network requests without freezing the interface.
- Use centralized error handling.
- Centralize application configuration.
- Avoid duplicated business logic.
- Use environment variables for configurable settings.
- Do not hardcode API credentials, passwords, tokens, or secrets.
- Use appropriate logging.
- Keep the code maintainable and readable.

---

# 4. PHASE 3 — BACKEND AND API INTEGRATION

The desktop application must use the existing backend as its primary source of truth.

Do not create a separate database containing duplicate application records unless there is a verified architectural reason.

### API integration requirements

Build a reusable API client responsible for:

- HTTP GET requests.
- HTTP POST requests.
- HTTP PUT/PATCH requests.
- HTTP DELETE requests.
- Authentication headers.
- Request timeouts.
- Response parsing.
- Error handling.
- Connection status.
- Retry handling where appropriate.
- API response validation.

Use a suitable HTTP library such as `httpx` or another justified alternative.

### Database requirements

The desktop application must communicate with the database through the existing backend.

Do not connect directly to PostgreSQL or expose database credentials inside the desktop application.

All operations that modify application data must follow the backend's existing business rules and authorization checks.

### API compatibility

Inspect the existing API before implementation.

If an endpoint is missing:

1. Determine whether the functionality can be achieved using existing endpoints.
2. Identify the exact missing operation.
3. Determine whether a backend API extension is necessary.
4. Implement the smallest safe extension if the backend is within the project's scope.
5. Preserve compatibility with the existing web frontend.
6. Document every new or modified endpoint.

Do not create unnecessary endpoints or change the database schema without a clear technical justification.

### Configuration

The API base URL must be configurable.

Support separate development and production configurations.

Example:

```env
APP_ENV=development
API_BASE_URL=http://127.0.0.1:8000/api
REQUEST_TIMEOUT=30
```

Use actual values appropriate to the existing backend. The example above is only illustrative.

The application must not depend on a hardcoded localhost address when running in production.

---

# 5. PHASE 4 — AUTHENTICATION AND SECURITY

Reproduce the existing authentication workflow as closely as possible.

Inspect whether the web application uses:

- Email and password authentication.
- Google authentication.
- Apple authentication.
- Guest or anonymous access.
- OTP verification.
- Multi-factor authentication.
- Role-based access control.
- Token refresh mechanisms.

Implement only authentication methods supported by the existing system or that can be securely integrated.

### Security requirements

- Never store passwords in plaintext.
- Never hardcode API secrets.
- Use secure HTTPS connections in production.
- Validate authentication responses.
- Handle expired sessions.
- Handle token refresh where supported.
- Support logout and session invalidation.
- Prevent unauthorized access to protected views.
- Respect backend role permissions.
- Protect sensitive user information.
- Use secure operating-system credential storage where appropriate.
- Avoid exposing tokens in application logs.

If Google or Apple OAuth is supported, investigate a suitable desktop OAuth flow using an external browser and secure callback handling.

Do not simulate successful authentication.

Every authentication action must be connected to the actual backend or identity provider.

---

# 6. PHASE 5 — DESKTOP UI/UX DESIGN

Create a polished, professional desktop interface.

Do not simply copy the website's mobile layout.

Adapt the existing visual identity while designing an interface appropriate for desktop displays.

### Design expectations

- Clean and organized layout.
- Consistent spacing and typography.
- Professional color palette.
- Proper visual hierarchy.
- Persistent desktop navigation when appropriate.
- Responsive resizing for different window dimensions.
- Reusable UI components.
- Clear buttons and action states.
- Proper loading indicators.
- Empty states.
- Error states.
- Success notifications.
- Confirmation dialogs for destructive actions.
- Keyboard-friendly navigation where practical.

### Desktop navigation

Choose an appropriate navigation system based on the application's features.

Possible layouts include:

- Sidebar navigation.
- Top navigation bar.
- Dashboard layout.
- Multi-view navigation.
- Tab-based navigation.

Do not force a sidebar or dashboard if another layout is more appropriate.

### User experience requirements

Every visible interactive element must work.

Do not create decorative buttons that have no functionality.

Do not leave placeholder content, fake statistics, or simulated application records in the completed application.

Provide appropriate feedback when an action succeeds or fails.

Make sure that forms have validation and that destructive actions require confirmation.

### Visual consistency

Inspect the existing web application's:

- Logo.
- Color palette.
- Typography.
- Icons.
- Buttons.
- Cards.
- Navigation.
- Design language.

Reuse appropriate visual assets where possible.

Improve desktop usability without unnecessarily changing the application's identity.

---

# 7. PHASE 6 — IMPLEMENT THE APPLICATION FEATURES

Use the feature mapping document as the implementation checklist.

For every important feature in the existing web application:

1. Identify its corresponding desktop view.
2. Identify the required API endpoints.
3. Implement the interface.
4. Connect the interface to the backend.
5. Implement input validation.
6. Handle loading and error states.
7. Test the complete user workflow.
8. Update the feature mapping document.

### Feature completeness

A feature is not complete simply because its interface exists.

For example, a working registration feature must:

- Accept user input.
- Validate the input.
- Submit the actual request.
- Handle server responses.
- Display meaningful errors.
- Confirm successful registration.
- Integrate with the existing authentication system.

Apply the same principle to all application modules.

### Preserve existing business logic

Do not independently rewrite algorithms or business rules that already exist in the backend.

The desktop application should consume the backend's results rather than maintaining a separate implementation of the same rules.

For features that depend on browser-specific capabilities, identify suitable desktop alternatives.

Examples include:

- Geolocation.
- Maps.
- File uploads.
- OAuth redirects.
- Notifications.
- Camera or device permissions.

Implement a suitable desktop equivalent where feasible, and document any limitations.

---

# 8. PHASE 7 — ERROR HANDLING AND APPLICATION RELIABILITY

The desktop application must handle real-world failures.

Test and handle:

- No internet connection.
- Backend server unavailable.
- Invalid API responses.
- Request timeout.
- Expired authentication.
- Invalid credentials.
- Unauthorized operations.
- Missing data.
- Invalid user input.
- Failed file uploads.
- Failed downloads.
- Unexpected application exceptions.

The desktop application must not crash unnecessarily when a network request fails.

Display understandable error messages rather than exposing raw stack traces to ordinary users.

Log useful technical details for debugging without recording passwords, tokens, or other sensitive information.

### Offline functionality

First determine whether offline functionality is needed and whether it is supported by the existing system.

Do not claim that the application supports full offline functionality unless it has actually been implemented and tested.

Where offline behavior is implemented:

- Clearly distinguish cached information from live information.
- Define which operations are available offline.
- Define synchronization behavior.
- Handle synchronization failures.
- Prevent duplicate submissions.
- Address data conflicts.
- Do not silently overwrite newer server data.

---

# 9. PHASE 8 — TESTING, QA, AND QC

You are responsible for testing the desktop application, not merely writing its code.

Create a proper test plan and execute the tests that can be performed in the current environment.

### Functional testing

Test:

- Application startup.
- Login and logout.
- User registration if supported.
- Navigation.
- Forms.
- Input validation.
- CRUD operations.
- Search.
- Filtering.
- Sorting.
- File operations.
- Settings.
- User permissions.
- Application shutdown.

Test every implemented feature from beginning to end.

### API integration testing

Verify:

- Correct API endpoints.
- Correct HTTP methods.
- Correct request payloads.
- Correct response handling.
- Correct authentication headers.
- Correct error handling.
- Correct data updates.
- Consistency between desktop and web clients.

### UI testing

Check:

- Window resizing.
- Layout consistency.
- Text overflow.
- Button behavior.
- Dialog behavior.
- Loading indicators.
- Empty states.
- Error messages.
- Navigation behavior.
- Keyboard interaction where supported.

### Security testing

Check:

- Token handling.
- Password handling.
- Unauthorized access.
- Role-based restrictions.
- Sensitive information exposure.
- API configuration.
- Production HTTPS usage.

### Automated testing

Use suitable tools such as:

- `pytest` for automated tests.
- Mock API responses for isolated service tests.
- Static analysis and linting tools.
- Appropriate Flet testing methods supported by the installed version.

Do not mark tests as passed unless they were actually executed successfully.

### Test report

Create:

`DESKTOP_APP_DOCUMENTATION/03_QA_QC_REPORT.md`

Include:

| Test Case | Expected Result | Actual Result | Status |
|---|---|---|---|
| Login with valid credentials | User successfully logs in | Observed result | Pass/Fail |
| Login with invalid credentials | Error is displayed | Observed result | Pass/Fail |
| Backend unavailable | Application handles connection failure | Observed result | Pass/Fail |

Also document:

- Bugs discovered.
- Bugs fixed.
- Remaining limitations.
- Unexecuted tests.
- Security concerns.
- Recommended improvements.

Fix discovered problems before declaring the application complete.

---

# 10. PHASE 9 — WINDOWS DESKTOP BUILD AND DISTRIBUTION

Prioritize Windows desktop deployment.

The final application should be buildable into a Windows executable or distributable package using the current officially supported Flet build process.

Before implementing the build process:

1. Check the installed Flet version.
2. Consult the current official Flet documentation.
3. Verify the correct build commands.
4. Verify required dependencies.
5. Determine the appropriate packaging configuration.

Do not rely on outdated Flet commands or APIs.

### Packaging requirements

Prepare:

- Application name.
- Application icon.
- Version information.
- Application assets.
- Dependency configuration.
- Production API configuration.
- Build instructions.
- Distribution instructions.

The final output should include a Windows desktop build when the current environment supports it.

If packaging cannot be completed because of an environmental limitation, explain the exact blocker and provide verified commands for building it on a compatible machine.

Do not claim that an executable was generated unless the actual file exists.

---

# 11. PHASE 10 — DOCUMENTATION

Maintain documentation throughout the development process.

Create the following files:

```text
DESKTOP_APP_DOCUMENTATION/
│
├── 01_EXISTING_SYSTEM_ANALYSIS.md
├── 02_FEATURE_MAPPING.md
├── 03_QA_QC_REPORT.md
├── 04_DESKTOP_ARCHITECTURE.md
├── 05_API_INTEGRATION.md
├── 06_AUTHENTICATION_AND_SECURITY.md
├── 07_INSTALLATION_GUIDE.md
├── 08_BUILD_AND_DISTRIBUTION.md
├── 09_KNOWN_LIMITATIONS.md
└── 10_DEVELOPMENT_CHANGELOG.md
```

The documentation must describe the actual implementation, not an imagined or proposed implementation.

Update the documentation whenever an architectural decision, feature, API integration, or major fix is made.

Include installation instructions that another developer can follow.

---

# 12. DEVELOPMENT RULES

Follow these rules throughout the development process:

1. Inspect before modifying.
2. Understand existing logic before implementing new logic.
3. Preserve the existing web application.
4. Do not delete existing files unnecessarily.
5. Do not overwrite important configuration files without checking their contents.
6. Do not introduce unnecessary dependencies.
7. Do not duplicate backend business logic.
8. Do not expose secrets.
9. Do not use mock data as a substitute for real functionality.
10. Do not leave visible controls unimplemented.
11. Do not ignore exceptions or failed requests.
12. Do not mark unexecuted tests as passed.
13. Do not use deprecated Flet APIs when a supported alternative exists.
14. Check official documentation when uncertain about framework behavior.
15. Keep the desktop application independent from the web frontend.
16. Preserve compatibility with the existing backend.
17. Record important development decisions.
18. Avoid unnecessary changes to the existing web application.

### Dependency management

Use compatible and stable dependencies.

Record the dependencies and versions in the appropriate project files.

Avoid installing packages simply because they are popular. Every additional dependency should have a clear purpose.

### Code quality

Write code that is:

- Readable.
- Modular.
- Maintainable.
- Properly structured.
- Consistently named.
- Documented where necessary.
- Compatible with the supported Python and Flet versions.

---

# 13. DEVELOPMENT EXECUTION STRATEGY

Follow this development order:

**Stage 1:** Inspect the existing system.

**Stage 2:** Document the architecture and identify integration requirements.

**Stage 3:** Map existing web features to desktop features.

**Stage 4:** Design the Flet desktop architecture.

**Stage 5:** Prepare the Python environment and dependencies.

**Stage 6:** Implement the API client and configuration.

**Stage 7:** Implement authentication and session management.

**Stage 8:** Build the main desktop layout and navigation.

**Stage 9:** Implement application features one module at a time.

**Stage 10:** Integrate every module with the actual backend.

**Stage 11:** Perform functional, integration, UI, and security testing.

**Stage 12:** Fix identified issues and perform regression testing.

**Stage 13:** Prepare the production configuration.

**Stage 14:** Build and verify the Windows desktop application.

**Stage 15:** Complete the documentation and final report.

At the end of each stage, update the documentation and identify any unresolved issues.

Do not skip stages simply to finish faster.

You may adjust the order when a technical dependency requires it, but document the reason.

---

# 14. FINAL ACCEPTANCE CRITERIA

The desktop application is considered complete only when the following conditions are satisfied:

- [ ] The existing system has been inspected.
- [ ] The desktop architecture is documented.
- [ ] The feature mapping is complete.
- [ ] The Flet project is properly structured.
- [ ] The application launches successfully.
- [ ] The interface is designed for desktop use.
- [ ] Authentication is connected to the real authentication system.
- [ ] The application communicates with the existing backend.
- [ ] Important existing features are implemented.
- [ ] Data operations use the existing backend.
- [ ] Error handling works.
- [ ] Security measures are implemented.
- [ ] Functional tests have been executed.
- [ ] API integration tests have been executed.
- [ ] UI testing has been performed.
- [ ] Identified bugs have been addressed.
- [ ] The desktop application does not break the existing web application.
- [ ] The Windows build has been generated and verified, or its exact environmental blocker is documented.
- [ ] Installation and usage instructions are available.
- [ ] Development and QA documentation are complete.

---

# 15. FINAL INSTRUCTIONS TO ANTIGRAVITY

Start by inspecting the currently opened workspace.

Do not ask me to explain components that you can identify by inspecting the source code and existing documentation.

Make reasonable technical decisions based on the actual project.

If you encounter uncertainty, investigate the existing implementation and official documentation before making assumptions.

If an integration is genuinely blocked, document the exact missing requirement and continue with the other independent tasks rather than abandoning the entire project.

Do not perform destructive database operations, overwrite production data, expose secrets, or make irreversible changes to the existing web application.

Do not stop at producing a plan, architecture diagram, UI mockup, or sample code.

**Your main responsibility is to actually DEVELOP, INTEGRATE, RUN, TEST, DEBUG, AND DOCUMENT the Python Flet desktop application.**

At the end, provide a final development report containing:

1. What was inspected.
2. What was developed.
3. Features successfully implemented.
4. Backend integrations completed.
5. Files and folders created or modified.
6. Tests executed and their actual results.
7. Bugs fixed.
8. Remaining limitations.
9. Instructions for running the application.
10. Instructions for building the Windows executable.
11. Location of the generated desktop application, if successfully built.

Be transparent about incomplete work. Never describe a feature as functional unless it has been implemented and verified.

Begin with Phase 1 now.