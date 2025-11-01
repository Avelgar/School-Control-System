const { createApp } = Vue;
import { API_BASE_URL } from './config.js';

createApp({
    data() {
        return {
            isLoading: true,
            userProfile: null,
            userCourses: [],
            userStats: {},
            completedTests: [],
            studentStats: {},
            studentTestDetails: [],

            showTestsModal: false,
            showTestResultModal: false,
            showCompletedTestsModal: false,
            selectedCourse: null,
            studentCourseTests: [],
            testsLoading: false,
            selectedTest: null,
            testScore: 0,

            teacherCourseStats: {},
            showCourseStatistics: false,
            selectedCourseForStats: null,
            courseStatistics: {},
            statsLoading: false,
            showCourseTestsModal: false,
            selectedCourseForTests: null,
            teacherCourseTests: [],
            teacherTestsLoading: false,

            showUsersManagementModal: false,
            showUserFormModal: false,
            allUsers: [],
            allGroups: [],
            usersLoading: false,
            userFormLoading: false,
            editingUser: null,
            userForm: {
                fio: '',
                login: '',
                email: '',
                password: '',
                role: 'student',
                group_id: null
            },
            
            showGroupsManagementModal: false,
            showTestsManagementModal: false,
            showCoursesManagementModal: false,
            showGroupFormModal: false,
            showTestFormModal: false,
            showCourseFormModal: false,
            allTests: [],
            allCourses: [],
            allTeachers: [],
            groupsLoading: false,
            coursesLoading: false,
            groupFormLoading: false,
            testFormLoading: false,
            courseFormLoading: false,
            editingGroup: null,
            editingTest: null,
            editingCourse: null,
            groupForm: {
                name: ''
            },
            testForm: {
                name: '',
                course_id: null
            },
            courseForm: {
                name: '',
                teacher_id: null,
                group_id: null
            },
        };
    },
    async mounted() {
        await this.checkAuthentication();
        if (this.userProfile) {
            await this.loadUserData();
        }
    },
    methods: {
        async checkAuthentication() {
            const token = localStorage.getItem('authToken');
            
            if (!token) {
                this.redirectToLogin();
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE_URL}/auth/me`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.userProfile = await response.json();
                    this.isLoading = false;
                } else {
                    this.clearAuthData();
                    this.redirectToLogin();
                }
            } catch (error) {
                console.error('Auth check error:', error);
                this.clearAuthData();
                this.redirectToLogin();
            }
        },

        async loadUserData() {
            try {
                await this.loadCourses();
                
                if (this.userProfile.role === 'student') {
                    await this.loadStudentData();
                } else if (this.userProfile.role === 'teacher') {
                    await this.loadTeacherStats();
                } else if (this.userProfile.role === 'admin') {
                    await this.loadAdminStats();
                }
            } catch (error) {
                console.error('Error loading user data:', error);
                alert('Ошибка загрузки данных');
            }
        },

        async loadCourses() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/courses/my`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.userCourses = await response.json();
                }
            } catch (error) {
                console.error('Error loading courses:', error);
            }
        },

        async loadStudentData() {
            try {
                await this.loadStudentStats();
                await this.loadCompletedTestsDetails();
            } catch (error) {
                console.error('Error loading student data:', error);
            }
        },

        async loadStudentStats() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/student/stats`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.studentStats = await response.json();
                }
            } catch (error) {
                console.error('Error loading student stats:', error);
            }
        },

        async loadCompletedTestsDetails() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/student/completed-tests`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.studentTestDetails = await response.json();
                }
            } catch (error) {
                console.error('Error loading completed tests details:', error);
            }
        },

        async loadTeacherStats() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/teacher/stats`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.userStats = await response.json();
                }
            } catch (error) {
                console.error('Error loading teacher stats:', error);
            }
        },

        async loadAdminStats() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/stats`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.userStats = await response.json();
                }
            } catch (error) {
                console.error('Error loading admin stats:', error);
            }
        },

        getRoleName(role) {
            const roles = {
                'student': 'Студент',
                'teacher': 'Преподаватель', 
                'admin': 'Администратор'
            };
            return roles[role] || role;
        },

        getCompletedTestsCount() {
            return this.completedTests.length;
        },
        
        clearAuthData() {
            localStorage.removeItem('authToken');
        },
        
        redirectToLogin() {
            window.location.href = '/';
        },
        
        logout() {
            this.clearAuthData();
            window.location.href = '/';
        },

        // ========== МЕТОДЫ ДЛЯ СТУДЕНТОВ ==========
        async openTestsModal(course) {
            this.selectedCourse = course;
            this.showTestsModal = true;
            await this.loadStudentCourseTests(course.id);
        },

        closeTestsModal() {
            this.showTestsModal = false;
            this.selectedCourse = null;
            this.studentCourseTests = [];
        },

        async loadStudentCourseTests(courseId) {
            this.testsLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/courses/${courseId}/tests-with-completion`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.studentCourseTests = await response.json();
                } else {
                    console.error('Failed to load course tests');
                    alert('Ошибка загрузки тестов');
                }
            } catch (error) {
                console.error('Error loading course tests:', error);
                alert('Ошибка загрузки тестов');
            } finally {
                this.testsLoading = false;
            }
        },

        openTestResultModal(test) {
            this.selectedTest = test;
            this.testScore = 0;
            this.showTestResultModal = true;
        },

        closeTestResultModal() {
            this.showTestResultModal = false;
            this.selectedTest = null;
            this.testScore = 0;
        },

        async submitTestResult() {
            if (this.testScore < 0 || this.testScore > 10) {
                alert('Балл должен быть от 0 до 10');
                return;
            }

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/completed-tests`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        test_id: this.selectedTest.id,
                        score: this.testScore
                    })
                });

                if (response.ok) {
                    alert('Результат теста сохранен!');
                    this.closeTestResultModal();

                    await this.loadStudentCourseTests(this.selectedCourse.id);
                    await this.loadStudentStats();
                    await this.loadCompletedTestsDetails();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка сохранения результата');
                }
            } catch (error) {
                console.error('Error submitting test result:', error);
                alert('Ошибка сохранения результата');
            }
        },

        getTestStatus(test) {
            if (test.completed) {
                return `Пройден: ${test.score}/10`;
            } else {
                return 'Не пройден';
            }
        },

        getTestStatusClass(test) {
            if (test.completed) {
                if (test.score >= 8) return 'status-success';
                else if (test.score >= 6) return 'status-warning';
                else return 'status-error';
            }
            return 'status-pending';
        },

        openCompletedTestsModal() {
            this.showCompletedTestsModal = true;
        },

        closeCompletedTestsModal() {
            this.showCompletedTestsModal = false;
        },

        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString('ru-RU');
        },

        // ========== МЕТОДЫ ДЛЯ ПРЕПОДАВАТЕЛЕЙ ==========
        async openCourseStatistics(course) {
            this.selectedCourseForStats = course;
            this.showCourseStatistics = true;
            await this.loadCourseStatistics(course.id);
        },

        closeCourseStatistics() {
            this.showCourseStatistics = false;
            this.selectedCourseForStats = null;
            this.courseStatistics = {};
        },

        async loadCourseStatistics(courseId) {
            this.statsLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/teacher/courses/${courseId}/statistics`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.courseStatistics = await response.json();
                } else {
                    console.error('Failed to load course statistics');
                    alert('Ошибка загрузки статистики курса');
                }
            } catch (error) {
                console.error('Error loading course statistics:', error);
                alert('Ошибка загрузки статистики курса');
            } finally {
                this.statsLoading = false;
            }
        },

        formatLastActivity(dateString) {
            if (!dateString) return 'Нет активности';
            return new Date(dateString).toLocaleDateString('ru-RU');
        },

        async openCourseTestsModal(course) {
            this.selectedCourseForTests = course;
            this.showCourseTestsModal = true;
            await this.loadTeacherCourseTests(course.id);
        },

        closeCourseTestsModal() {
            this.showCourseTestsModal = false;
            this.selectedCourseForTests = null;
            this.teacherCourseTests = [];
        },

        async loadTeacherCourseTests(courseId) {
            this.teacherTestsLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/teacher/courses/${courseId}/tests`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.teacherCourseTests = await response.json();
                } else {
                    console.error('Failed to load course tests for teacher');
                    alert('Ошибка загрузки тестов курса');
                }
            } catch (error) {
                console.error('Error loading course tests for teacher:', error);
                alert('Ошибка загрузки тестов курса');
            } finally {
                this.teacherTestsLoading = false;
            }
        },

        formatTestDate(dateString) {
            return new Date(dateString).toLocaleDateString('ru-RU');
        },

        // ========== ОБЩИЕ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
        getProgressColor(percentage) {
            if (percentage >= 80) return '#27ae60';
            if (percentage >= 60) return '#f39c12';
            return '#e74c3c';
        },

        getScoreColor(score) {
            if (score >= 8) return '#27ae60';
            if (score >= 6) return '#f39c12';
            return '#e74c3c';
        },

        getCompletionStatus(percentage) {
            if (percentage >= 80) return 'status-high';
            if (percentage >= 60) return 'status-medium';
            return 'status-low';
        },

        getCompletionStatusText(percentage) {
            if (percentage >= 80) return 'Высокий';
            if (percentage >= 60) return 'Средний';
            if (percentage >= 1) return 'Низкий';
            return 'Не начат';
        },
        getCompletionColor(percentage) {
            return this.getProgressColor(percentage);
        },

         async openUsersManagementModal() {
            this.showUsersManagementModal = true;
            await this.loadAllUsers();
            await this.loadAllGroups();
        },

        closeUsersManagementModal() {
            this.showUsersManagementModal = false;
            this.allUsers = [];
            this.allGroups = [];
        },

        openAddUserModal() {
            this.editingUser = null;
            this.resetUserForm();
            this.showUserFormModal = true;
        },

        openEditUserModal(user) {
            this.editingUser = user;
            this.userForm = {
                fio: user.fio,
                login: user.login,
                email: user.email,
                password: '',
                role: user.role,
                group_id: user.group ? user.group.id : user.group_id
            };
            this.showUserFormModal = true;
        },

        closeUserFormModal() {
            this.showUserFormModal = false;
            this.editingUser = null;
            this.resetUserForm();
        },

        resetUserForm() {
            this.userForm = {
                fio: '',
                login: '',
                email: '',
                password: '',
                role: 'student',
                group_id: null
            };
        },
        
        async loadAllGroups() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/groups`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.allGroups = await response.json();
                } else {
                    console.error('Failed to load groups');
                }
            } catch (error) {
                console.error('Error loading groups:', error);
            }
        },

        async loadAllUsers() {
            this.usersLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const users = await response.json();

                    const groupsResponse = await fetch(`${API_BASE_URL}/api/groups`, {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (groupsResponse.ok) {
                        const groups = await groupsResponse.json();

                        this.allUsers = users.map(user => ({
                            ...user,
                            group: groups.find(g => g.id === user.group_id) || null
                        }));
                    } else {
                        this.allUsers = users;
                    }
                } else {
                    console.error('Failed to load users');
                    alert('Ошибка загрузки пользователей');
                }
            } catch (error) {
                console.error('Error loading users:', error);
                alert('Ошибка загрузки пользователей');
            } finally {
                this.usersLoading = false;
            }
        },

        async submitUserForm() {
            this.userFormLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const url = this.editingUser 
                    ? `${API_BASE_URL}/api/admin/users/${this.editingUser.id}`
                    : `${API_BASE_URL}/api/admin/users`;
                
                const method = this.editingUser ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(this.userForm)
                });

                if (response.ok) {
                    alert(this.editingUser ? 'Пользователь обновлен!' : 'Пользователь добавлен!');
                    this.closeUserFormModal();
                    await this.loadAllUsers();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка сохранения пользователя');
                }
            } catch (error) {
                console.error('Error saving user:', error);
                alert('Ошибка сохранения пользователя');
            } finally {
                this.userFormLoading = false;
            }
        },

        async deleteUser(user) {
            if (user.id === this.userProfile.id) {
                alert('Нельзя удалить самого себя');
                return;
            }

            let warningMessage = `Вы уверены, что хотите удалить пользователя "${user.fio}"?`;

            if (user.role === 'teacher') {
                warningMessage += '\n\nВНИМАНИЕ: Будут также удалены все курсы этого преподавателя и связанные тесты!';
            } else if (user.role === 'student') {
                warningMessage += '\n\nВНИМАНИЕ: Будут также удалены все пройденные тесты этого студента!';
            }

            if (!confirm(warningMessage)) {
                return;
            }

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/users/${user.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    alert('Пользователь удален!');
                    await this.loadAllUsers();
                } else {
                    let errorText;
                    try {
                        const errorData = await response.json();
                        errorText = errorData.detail || 'Ошибка удаления пользователя';
                    } catch {
                        errorText = await response.text();
                    }
                    alert(errorText);
                }
            } catch (error) {
                console.error('Error deleting user:', error);
                alert('Ошибка удаления пользователя: ' + error.message);
            }
        },
        
        async openGroupsManagementModal() {
            this.showGroupsManagementModal = true;
            await this.loadAllGroups();
        },

        closeGroupsManagementModal() {
            this.showGroupsManagementModal = false;
            this.allGroups = [];
        },

        openAddGroupModal() {
            this.editingGroup = null;
            this.resetGroupForm();
            this.showGroupFormModal = true;
        },

        openEditGroupModal(group) {
            this.editingGroup = group;
            this.groupForm = {
                name: group.name
            };
            this.showGroupFormModal = true;
        },

        closeGroupFormModal() {
            this.showGroupFormModal = false;
            this.editingGroup = null;
            this.resetGroupForm();
        },

        resetGroupForm() {
            this.groupForm = {
                name: ''
            };
        },

        async loadAllGroups() {
            this.groupsLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/groups`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.allGroups = await response.json();
                } else {
                    console.error('Failed to load groups');
                    alert('Ошибка загрузки групп');
                }
            } catch (error) {
                console.error('Error loading groups:', error);
                alert('Ошибка загрузки групп');
            } finally {
                this.groupsLoading = false;
            }
        },

        async submitGroupForm() {
            this.groupFormLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const url = this.editingGroup ? 
                    `${API_BASE_URL}/api/admin/groups/${this.editingGroup.id}` : 
                    `${API_BASE_URL}/api/admin/groups`;
                const method = this.editingGroup ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(this.groupForm)
                });

                if (response.ok) {
                    alert(this.editingGroup ? 'Группа обновлена!' : 'Группа добавлена!');
                    this.closeGroupFormModal();
                    await this.loadAllGroups();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка сохранения группы');
                }
            } catch (error) {
                console.error('Error saving group:', error);
                alert('Ошибка сохранения группы');
            } finally {
                this.groupFormLoading = false;
            }
        },

        async deleteGroup(group) {
            if (!confirm(`Удалить группу "${group.name}"?\n\nВНИМАНИЕ: Все пользователи этой группы будут отвязаны от группы.`)) {
                return;
            }

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/groups/${group.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    alert('Группа удалена!');
                    await this.loadAllGroups();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка удаления группы');
                }
            } catch (error) {
                console.error('Error deleting group:', error);
                alert('Ошибка удаления группы');
            }
        },

        // ========== МЕТОДЫ ДЛЯ УПРАВЛЕНИЯ ТЕСТАМИ ==========
        async openTestsManagementModal() {
            this.showTestsManagementModal = true;
            await this.loadAllTests();
            await this.loadAllCourses();
        },

        closeTestsManagementModal() {
            this.showTestsManagementModal = false;
            this.allTests = [];
        },

        openAddTestModal() {
            this.editingTest = null;
            this.resetTestForm();
            this.showTestFormModal = true;
        },

        openEditTestModal(test) {
            this.editingTest = test;
            this.testForm = {
                name: test.name,
                course_id: test.course_id
            };
            this.showTestFormModal = true;
        },

        closeTestFormModal() {
            this.showTestFormModal = false;
            this.editingTest = null;
            this.resetTestForm();
        },

        resetTestForm() {
            this.testForm = {
                name: '',
                course_id: null
            };
        },

        async loadAllTests() {
            this.testsLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/tests`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.allTests = await response.json();
                } else {
                    console.error('Failed to load tests');
                    alert('Ошибка загрузки тестов');
                }
            } catch (error) {
                console.error('Error loading tests:', error);
                alert('Ошибка загрузки тестов');
            } finally {
                this.testsLoading = false;
            }
        },

        async submitTestForm() {
            this.testFormLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const url = this.editingTest ? 
                    `${API_BASE_URL}/api/admin/tests/${this.editingTest.id}` : 
                    `${API_BASE_URL}/api/admin/tests`;
                const method = this.editingTest ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(this.testForm)
                });

                if (response.ok) {
                    alert(this.editingTest ? 'Тест обновлен!' : 'Тест добавлен!');
                    this.closeTestFormModal();
                    await this.loadAllTests();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка сохранения теста');
                }
            } catch (error) {
                console.error('Error saving test:', error);
                alert('Ошибка сохранения теста');
            } finally {
                this.testFormLoading = false;
            }
        },

        async deleteTest(test) {
            if (!confirm(`Удалить тест "${test.name}"?\n\nВНИМАНИЕ: Будут также удалены все результаты прохождения этого теста.`)) {
                return;
            }

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/tests/${test.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    alert('Тест удален!');
                    await this.loadAllTests();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка удаления теста');
                }
            } catch (error) {
                console.error('Error deleting test:', error);
                alert('Ошибка удаления теста');
            }
        },

        // ========== МЕТОДЫ ДЛЯ УПРАВЛЕНИЯ КУРСАМИ ==========
        async openCoursesManagementModal() {
            this.showCoursesManagementModal = true;
            await this.loadAllCourses();
            await this.loadAllGroups();
            await this.loadAllTeachers();
        },

        closeCoursesManagementModal() {
            this.showCoursesManagementModal = false;
            this.allCourses = [];
        },

        openAddCourseModal() {
            this.editingCourse = null;
            this.resetCourseForm();
            this.showCourseFormModal = true;
        },

        openEditCourseModal(course) {
            this.editingCourse = course;
            this.courseForm = {
                name: course.name,
                teacher_id: course.teacher_id,
                group_id: course.group_id
            };
            this.showCourseFormModal = true;
        },

        closeCourseFormModal() {
            this.showCourseFormModal = false;
            this.editingCourse = null;
            this.resetCourseForm();
        },

        resetCourseForm() {
            this.courseForm = {
                name: '',
                teacher_id: null,
                group_id: null
            };
        },

        async loadAllCourses() {
            this.coursesLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/courses`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.allCourses = await response.json();
                } else {
                    console.error('Failed to load courses');
                    alert('Ошибка загрузки курсов');
                }
            } catch (error) {
                console.error('Error loading courses:', error);
                alert('Ошибка загрузки курсов');
            } finally {
                this.coursesLoading = false;
            }
        },

        async loadAllTeachers() {
            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const users = await response.json();
                    this.allTeachers = users.filter(user => user.role === 'teacher');
                } else {
                    console.error('Failed to load teachers');
                }
            } catch (error) {
                console.error('Error loading teachers:', error);
            }
        },

        async submitCourseForm() {
            this.courseFormLoading = true;
            try {
                const token = localStorage.getItem('authToken');
                const url = this.editingCourse ? 
                    `${API_BASE_URL}/api/admin/courses/${this.editingCourse.id}` : 
                    `${API_BASE_URL}/api/admin/courses`;
                const method = this.editingCourse ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(this.courseForm)
                });

                if (response.ok) {
                    alert(this.editingCourse ? 'Курс обновлен!' : 'Курс добавлен!');
                    this.closeCourseFormModal();
                    await this.loadAllCourses();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка сохранения курса');
                }
            } catch (error) {
                console.error('Error saving course:', error);
                alert('Ошибка сохранения курса');
            } finally {
                this.courseFormLoading = false;
            }
        },

        async deleteCourse(course) {
            if (!confirm(`Удалить курс "${course.name}"?\n\nВНИМАНИЕ: Будут также удалены все тесты этого курса и результаты их прохождения.`)) {
                return;
            }

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE_URL}/api/admin/courses/${course.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    alert('Курс удален!');
                    await this.loadAllCourses();
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка удаления курса');
                }
            } catch (error) {
                console.error('Error deleting course:', error);
                alert('Ошибка удаления курса');
            }
        }
    }
}).mount('#main-app');