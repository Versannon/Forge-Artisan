using UnityEngine;

namespace ForgeArtisan
{
    /// <summary>
    /// ForgeArtisan First-Person Playable Character Controller.
    /// Allows the user to freely explore, climb stairs, walk through rooms,
    /// and interact with procedurally generated 3D environments in Unity Play Mode.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class ForgeArtisanPlayerController : MonoBehaviour
    {
        [Header("Locomotion")]
        public float walkSpeed = 5.0f;
        public float sprintSpeed = 8.5f;
        public float jumpHeight = 1.35f;
        public float gravity = -20.0f;

        [Header("Mouse Look")]
        public float mouseSensitivity = 2.0f;
        public float minPitch = -85.0f;
        public float maxPitch = 85.0f;

        [Header("Head & Camera")]
        public Camera playerCamera;
        public float eyeHeight = 1.65f;

        [Header("Perspective (1st / 3rd Person)")]
        public bool isThirdPerson = true;
        public float thirdPersonDistance = 3.5f;
        public float thirdPersonHeight = 2.0f;

        private CharacterController _controller;
        private Vector3 _velocity;
        private float _pitch = 10f;
        private bool _isGrounded;
        private GameObject _avatarVisual;

        private void Awake()
        {
            _controller = GetComponent<CharacterController>();
            ConfigureController();
        }

        private void Start()
        {
            if (playerCamera == null)
            {
                playerCamera = GetComponentInChildren<Camera>();
            }

            var childVis = transform.Find("AvatarVisual");
            if (childVis != null) _avatarVisual = childVis.gameObject;

            UpdateCameraView();

            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }

        private void UpdateCameraView()
        {
            if (playerCamera == null) return;
            playerCamera.nearClipPlane = 0.05f;
            if (isThirdPerson)
            {
                playerCamera.transform.localPosition = new Vector3(0, thirdPersonHeight, -thirdPersonDistance);
                if (_avatarVisual != null) _avatarVisual.SetActive(true);
            }
            else
            {
                playerCamera.transform.localPosition = new Vector3(0, eyeHeight, 0);
                if (_avatarVisual != null) _avatarVisual.SetActive(false);
            }
        }

        private void ConfigureController()
        {
            if (_controller == null) return;
            _controller.stepOffset = 0.45f; // Enables smooth stair climbing
            _controller.slopeLimit = 50.0f;
            _controller.height = 1.8f;
            _controller.radius = 0.35f;
            _controller.center = new Vector3(0, 0.9f, 0);
            _controller.skinWidth = 0.05f;
        }

        private void Update()
        {
            // Perspective toggle (1st person / 3rd person)
            if (Input.GetKeyDown(KeyCode.V))
            {
                isThirdPerson = !isThirdPerson;
                UpdateCameraView();
            }

            // Cursor lock toggle
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
            else if (Input.GetMouseButtonDown(0) && Cursor.lockState != CursorLockMode.Locked)
            {
                Cursor.lockState = CursorLockMode.Locked;
                Cursor.visible = false;
            }

            if (Cursor.lockState == CursorLockMode.Locked)
            {
                HandleMouseLook();
            }

            HandleMovement();
            HandleInteraction();
        }

        private void HandleMouseLook()
        {
            float mouseX = Input.GetAxis("Mouse X") * mouseSensitivity;
            float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;

            // Horizontal rotation (Yaw)
            transform.Rotate(Vector3.up * mouseX);

            // Vertical rotation (Pitch)
            _pitch -= mouseY;
            _pitch = Mathf.Clamp(_pitch, minPitch, maxPitch);

            if (playerCamera != null)
            {
                playerCamera.transform.localEulerAngles = new Vector3(_pitch, 0, 0);
            }
        }

        private void HandleMovement()
        {
            _isGrounded = _controller.isGrounded;
            if (_isGrounded && _velocity.y < 0)
            {
                _velocity.y = -2.0f;
            }

            float moveX = Input.GetAxis("Horizontal");
            float moveZ = Input.GetAxis("Vertical");

            bool isSprinting = Input.GetKey(KeyCode.LeftShift);
            float currentSpeed = isSprinting ? sprintSpeed : walkSpeed;

            Vector3 moveDirection = (transform.right * moveX + transform.forward * moveZ).normalized;
            _controller.Move(moveDirection * currentSpeed * Time.deltaTime);

            // Jump
            if (Input.GetButtonDown("Jump") && _isGrounded)
            {
                _velocity.y = Mathf.Sqrt(jumpHeight * -2.0f * gravity);
            }

            // Gravity
            _velocity.y += gravity * Time.deltaTime;
            _controller.Move(_velocity * Time.deltaTime);
        }

        private void HandleInteraction()
        {
            if (Input.GetKeyDown(KeyCode.E) && playerCamera != null)
            {
                Ray ray = new Ray(playerCamera.transform.position, playerCamera.transform.forward);
                if (Physics.Raycast(ray, out RaycastHit hit, 3.5f))
                {
                    Debug.Log($"[ForgeArtisan Explorer] Interacted with: {hit.collider.gameObject.name}");
                }
            }
        }

        private void OnGUI()
        {
            // Control Overlay HUD
            GUI.color = new Color(0.08f, 0.12f, 0.18f, 0.88f);
            GUI.Box(new Rect(15, 15, 360, 118), GUIContent.none);
            GUI.color = Color.white;

            var titleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 13,
                fontStyle = FontStyle.Bold
            };
            titleStyle.normal.textColor = new Color(0.35f, 0.7f, 1.0f);

            var bodyStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11
            };
            bodyStyle.normal.textColor = Color.white;

            string viewMode = isThirdPerson ? "3rd Person (Follow)" : "1st Person (Head)";
            GUI.Label(new Rect(25, 20, 340, 20), $"🎮 Unity Explorer Mode — [{viewMode}]", titleStyle);
            GUI.Label(new Rect(25, 42, 340, 18), "• WASD / Arrows : Walk (Shift to Sprint)", bodyStyle);
            GUI.Label(new Rect(25, 60, 340, 18), "• Space : Jump   |  Mouse : Look Around", bodyStyle);
            GUI.Label(new Rect(25, 78, 340, 18), "• V : Toggle 1st / 3rd Person View", bodyStyle);
            GUI.Label(new Rect(25, 96, 340, 18), "• E : Interact   |  Esc : Release Cursor", bodyStyle);

            // Center Crosshair
            float cx = Screen.width * 0.5f;
            float cy = Screen.height * 0.5f;
            GUI.color = new Color(1f, 1f, 1f, 0.6f);
            GUI.Box(new Rect(cx - 2, cy - 2, 4, 4), GUIContent.none);
            GUI.color = Color.white;
        }
    }
}
